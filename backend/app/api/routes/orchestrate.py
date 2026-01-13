from fastapi import APIRouter, Depends
from redis import Redis
from uuid import uuid4
from app.queue.redis_queue import enqueue_task
from app.queue.tasks import Task
from app.db.session import get_redis
from app.core.logging import get_logger

orchestrate_router = APIRouter()
logger = get_logger(__name__)

@orchestrate_router.post('/run/all')
async def run_all(redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    logger.info("Orchestration started", extra={"event": "run_all", "trace_id": trace_id})

    # Simulate enqueuing N tasks
    for i in range(5):
        enqueue_task(redis, Task(trace_id=trace_id, task_type="scrape", payload={"n": i}))
        enqueue_task(redis, Task(trace_id=trace_id, task_type="extract", payload={"n": i}))

    return {"status": "enqueued", "trace_id": trace_id}