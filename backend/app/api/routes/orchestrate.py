from fastapi import APIRouter, Depends
from redis import Redis
from uuid import uuid4
from app.queue.redis_queue import enqueue_task
from app.core.request_context import set_trace_id, clear_trace_id
from app.queue.tasks import Task
from app.db.session import get_redis
from app.core.logging import get_logger

orchestrate_router = APIRouter()
logger = get_logger(__name__)

def _enqueue_dummy(redis: Redis, trace_id: str, task_type: str, n: int) -> None:
    task = Task(
        task_id=str(uuid4()),
        trace_id=trace_id,
        task_type=task_type,
        attempt=0,
        payload={"n": n},
    )
    enqueue_task(redis, task)
    logger.info("task_enqueued", extra={"event": "queue.enqueue", "task_type": task_type, "task_id": task.task_id})

@orchestrate_router.post("/run/all", tags=["orchestrate"])
async def run_all(redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        logger.info("run_all_start", extra={"event": "api.run_all_start"})

        for i in range(5):
            _enqueue_dummy(redis, trace_id, "scrape", i)
            _enqueue_dummy(redis, trace_id, "extract", i)

        logger.info("run_all_done", extra={"event": "api.run_all_done"})
        return {"status": "enqueued", "trace_id": trace_id, "count": 10}
    finally:
        clear_trace_id()

@orchestrate_router.post("/run/scrape", tags=["orchestrate"])
async def run_scrape(redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        logger.info("run_scrape_start", extra={"event": "api.run_scrape_start"})
        for i in range(5):
            _enqueue_dummy(redis, trace_id, "scrape", i)
        logger.info("run_scrape_done", extra={"event": "api.run_scrape_done"})
        return {"status": "enqueued", "trace_id": trace_id, "count": 5}
    finally:
        clear_trace_id()


@orchestrate_router.post("/run/extract", tags=["orchestrate"])
async def run_extract(redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        logger.info("run_extract_start", extra={"event": "api.run_extract_start"})
        for i in range(5):
            _enqueue_dummy(redis, trace_id, "extract", i)
        logger.info("run_extract_done", extra={"event": "api.run_extract_done"})
        return {"status": "enqueued", "trace_id": trace_id, "count": 5}
    finally:
        clear_trace_id()
