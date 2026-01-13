import json
import time
from redis import Redis
from typing import Optional
from app.core.logging import get_logger
from app.queue.tasks import Task

logger = get_logger(__name__)
QUEUE_SCRAPE = "openfunnel:tasks:scrape"
QUEUE_EXTRACT = "openfunnel:tasks:extract"
INFLIGHT_SCRAPE = "openfunnel:inflight:scrape"
INFLIGHT_EXTRACT = "openfunnel:inflight:extract"
DLQ_SCRAPE = "openfunnel:dlq:scrape"
DLQ_EXTRACT = "openfunnel:dlq:extract"

def _q(task_type: str) -> str:
    if task_type == "scrape":
        return QUEUE_SCRAPE
    if task_type == "extract":
        return QUEUE_EXTRACT
    raise ValueError(f"Unknown task_type: {task_type}")


def _inflight(task_type: str) -> str:
    if task_type == "scrape":
        return INFLIGHT_SCRAPE
    if task_type == "extract":
        return INFLIGHT_EXTRACT
    raise ValueError(f"Unknown task_type: {task_type}")


def _dlq(task_type: str) -> str:
    if task_type == "scrape":
        return DLQ_SCRAPE
    if task_type == "extract":
        return DLQ_EXTRACT
    raise ValueError(f"Unknown task_type: {task_type}")

def enqueue_task(redis: Redis, task: Task) -> None:
    q = _q(task.task_type)
    redis.rpush(q, json.dumps(task.model_dump()))
    logger.info("task_enqueued", extra={"event": "queue.enqueue", "queue": q, "task_id": task.task_id})

def reserve_task(redis: Redis, task_type: str, block_seconds: int = 5) -> Optional[Task]:
    q = _q(task_type)
    inflight = _inflight(task_type)

    raw = redis.brpoplpush(q, inflight, timeout=block_seconds)
    if not raw:
        return None

    data = json.loads(raw)
    task = Task(**data)

    # stamp reserve time for stale detection
    task.reserved_at = int(time.time())
    redis.lset(inflight, -1, json.dumps(task.model_dump()))  # update last moved item

    logger.info(
        "task_reserved",
        extra={"event": "queue.reserve", "queue": q, "inflight": inflight, "task_id": task.task_id},
    )
    return task

def ack_task(redis: Redis, task: Task) -> None:
    inflight = _inflight(task.task_type)
    raw = json.dumps(task.model_dump())
    redis.lrem(inflight, 1, raw)
    logger.info("task_acked", extra={"event": "queue.ack", "inflight": inflight, "task_id": task.task_id})

def fail_task(redis: Redis, task: Task, *, error: str, max_attempts: int) -> None:
    """
    - increments attempt
    - if attempts remain -> requeue
    - else -> DLQ
    Always removes from inflight first.
    """
    inflight = _inflight(task.task_type)
    raw = json.dumps(task.model_dump())
    redis.lrem(inflight, 1, raw)

    task.attempt += 1
    task.last_error = error

    if task.attempt < max_attempts:
        enqueue_task(redis, task)
        logger.warning(
            "task_requeued",
            extra={"event": "queue.retry", "task_id": task.task_id, "attempt": task.attempt},
        )
        return

    dlq = _dlq(task.task_type)
    redis.rpush(dlq, json.dumps(task.model_dump()))
    logger.error(
        "task_dead_lettered",
        extra={"event": "queue.dlq", "task_id": task.task_id, "attempt": task.attempt, "dlq": dlq},
    )


def requeue_stale(redis: Redis, task_type: str, visibility_timeout_sec: int, max_to_requeue: int = 50) -> int:
    """
    Scan inflight list and requeue tasks whose reserved_at is too old.
    (Simple and good enough for the take-home.)
    """
    inflight = _inflight(task_type)
    now = int(time.time())
    requeued = 0

    items = redis.lrange(inflight, 0, max_to_requeue - 1)
    for raw in items:
        data = json.loads(raw)
        reserved_at = data.get("reserved_at") or 0
        if reserved_at and (now - reserved_at) > visibility_timeout_sec:
            # remove from inflight and requeue
            redis.lrem(inflight, 1, raw)
            redis.rpush(_q(task_type), raw)
            requeued += 1

    if requeued:
        logger.warning(
            "stale_requeued",
            extra={"event": "queue.requeue_stale", "task_type": task_type, "count": requeued},
        )

    return requeued