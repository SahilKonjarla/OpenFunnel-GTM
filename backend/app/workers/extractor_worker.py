import time
from redis import Redis
from app.queue.redis_queue import dequeue_task
from app.db.session import get_redis
from app.core.logging import init_logging, get_logger
from app.core.request_context import set_trace_id, clear_trace_id

init_logging("worker_extractor")
logger = get_logger(__name__)
r: Redis = get_redis()

while True:
    task = dequeue_task(r, task_type="extract", block_seconds=5)

    if not task:
        continue

    if task.task_type != "extract":
        continue

    set_trace_id(task.trace_id)
    logger.info("task_start", extra={"event": "task_start", "task_id": task.task_id, "task_type": task.task_type})

    try:
        # Simulate some work
        time.sleep(1)
        logger.info("task_ok", extra={"event": "task_ok", "task_id": task.task_id, "task_type": task.task_type})
    except Exception:
        logger.exception("task_fail", extra={"event": "task_fail", "task_id": task.task_id, "task_type": task.task_type})
    finally:
        clear_trace_id()