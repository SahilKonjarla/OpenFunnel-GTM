from fastapi import APIRouter, Depends
from redis import Redis

from app.core.logging import get_logger
from app.db.session import get_redis
from app.queue.redis_queue import (
    QUEUE_SCRAPE,
    QUEUE_EXTRACT,
    INFLIGHT_SCRAPE,
    INFLIGHT_EXTRACT,
    DLQ_SCRAPE,
    DLQ_EXTRACT,
)

debug_queue_router = APIRouter(prefix="/debug/queue", tags=["debug"])
logger = get_logger(__name__)


@debug_queue_router.get("/stats")
def stats(redis: Redis = Depends(get_redis)):
    out = {
        "queue_scrape": redis.llen(QUEUE_SCRAPE),
        "queue_extract": redis.llen(QUEUE_EXTRACT),
        "inflight_scrape": redis.llen(INFLIGHT_SCRAPE),
        "inflight_extract": redis.llen(INFLIGHT_EXTRACT),
        "dlq_scrape": redis.llen(DLQ_SCRAPE),
        "dlq_extract": redis.llen(DLQ_EXTRACT),
    }
    logger.info("queue_stats", extra={"event": "debug.queue_stats", **out})
    return out


@debug_queue_router.get("/dlq/{task_type}")
def dlq_peek(task_type: str, redis: Redis = Depends(get_redis)):
    if task_type == "scrape":
        key = DLQ_SCRAPE
    elif task_type == "extract":
        key = DLQ_EXTRACT
    else:
        return {"error": "task_type must be scrape|extract"}

    items = redis.lrange(key, 0, 9)  # first 10
    logger.info("dlq_peek", extra={"event": "debug.dlq_peek", "task_type": task_type, "count": len(items)})
    return {"task_type": task_type, "count": len(items), "items": items}
