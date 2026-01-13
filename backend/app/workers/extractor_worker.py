import time
from redis import Redis
from app.queue.redis_queue import dequeue_task
from app.queue.tasks import Task
from app.db.session import get_redis
from app.core.logging import init_logging, get_logger
from app.core.request_context import set_trace_id, clear_trace_id

init_logging("extractor_worker")
logger = get_logger(__name__)
redis: Redis = get_redis()

while True:
    task = dequeue_task(redis)

    if not task:
        time.sleep(0.5)
        continue

    if task.task_type != "extract":
        continue

    set_trace_id(task.trace_id)
    logger.info("task_start", extra={"event": "task_start", "task_id": task.task_id})

    try:
        # Simulate some work
        time.sleep(1)
        logger.info("task_ok", extra={"event": "task_ok", "task_id": task.task_id})
    except Exception as e:
        logger.error("task_fail", extra={"event": "task_fail", "task_id": task.task_id, "error": str(e)})
    finally:
        clear_trace_id()