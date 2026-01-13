import json
from redis import Redis
from typing import Optional
from app.core.logging import get_logger
from app.queue.tasks import Task

logger = get_logger(__name__)
QUEUE_SCRAPE = "openfunnel:tasks:scrape"
QUEUE_EXTRACT = "openfunnel:tasks:extract"

def _queue_for(task_type: str) -> str:
    if task_type == "scrape":
        return QUEUE_SCRAPE
    if task_type == "extract":
        return QUEUE_EXTRACT
    raise ValueError(f"Unknown task_type: {task_type}")

def enqueue_task(redis: Redis, task: Task) -> None:
    q = _queue_for(task.task_type)
    redis.rpush(q, json.dumps(task.model_dump()))
    logger.info(
        "task_enqueued",
        extra={"event": "queue.enqueue", "queue": q, "task_id": task.task_id, "task_type": task.task_type},
    )

def dequeue_task(redis: Redis, task_type: str, block_seconds: int = 5) -> Optional[Task]:
    q = _queue_for(task_type)
    result = redis.brpop(q, timeout=block_seconds)
    if not result:
        return None

    _, task_json = result
    data = json.loads(task_json)
    task = Task(**data)

    logger.info(
        "task_dequeued",
        extra={"event": "queue.dequeue", "queue": q, "task_id": task.task_id, "task_type": task.task_type},
    )
    return task