import json
from redis import Redis
from app.core.logging import get_logger
from app.queue.tasks import Task

logger = get_logger(__name__)
QUEUE_NAME = "openfunnel-tasks"

def enqueue_task(redis: Redis, task: Task) -> None:
    redis.rpush(QUEUE_NAME, json.dumps(task.dict()))
    logger.info("Enqueued task", extra={"event": "enqueue", "task_id": task.task_id, "task_type": task.task_type})

def dequeue_task(redis: Redis) -> Task | None:
    task_json = redis.lpop(QUEUE_NAME)
    if task_json:
        data = json.loads(task_json)
        return Task(**data)
    return None