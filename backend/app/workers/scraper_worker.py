import time
from redis import Redis
from app.core.config import settings
from app.queue.redis_queue import reserve_task, ack_task, fail_task
from app.db.session import get_redis
from app.core.logging import init_logging, get_logger
from app.core.request_context import set_trace_id, clear_trace_id

init_logging("worker_scraper")
logger = get_logger(__name__)
r: Redis = get_redis()

while True:
    task = reserve_task(r, task_type="scrape", block_seconds=5)
    if not task:
        continue

    set_trace_id(task.trace_id)
    logger.info(
        "task_start",
        extra={
            "event": "task_start",
            "task_id": task.task_id,
            "task_type": task.task_type,
            "run_id": task.run_id,
            "job_posting_id": task.job_posting_id,
            "attempt": task.attempt,
        },
    )

    try:
        # Simulate some work
        time.sleep(1)
        ack_task(r, task)
        logger.info(
            "task_ok",
            extra={
                "event": "task_ok",
                "task_id": task.task_id,
                "task_type": task.task_type,
                "run_id": task.run_id,
                "job_posting_id": task.job_posting_id,
                "attempt": task.attempt,
            },
        )
    except Exception as e:
        fail_task(r, task, error=str(e), max_attempts=settings.max_attempts)
        logger.exception(
            "task_fail",
            extra={
                "event": "task_fail",
                "task_id": task.task_id,
                "task_type": task.task_type,
                "run_id": task.run_id,
                "job_posting_id": task.job_posting_id,
                "attempt": task.attempt,
            },
        )
    finally:
        clear_trace_id()
