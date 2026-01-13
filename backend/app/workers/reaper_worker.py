import time
from redis import Redis
from app.core.config import settings
from app.core.logging import init_logging, get_logger
from app.db.session import get_redis
from app.queue.redis_queue import requeue_stale

init_logging("worker_reaper")
logger = get_logger(__name__)
r: Redis = get_redis()

POLL_SEC = 5

while True:
    try:
        n1 = requeue_stale(
            r,
            task_type="scrape",
            visibility_timeout_sec=settings.visibility_timeout_sec,
            max_to_requeue=100,
        )
        n2 = requeue_stale(
            r,
            task_type="extract",
            visibility_timeout_sec=settings.visibility_timeout_sec,
            max_to_requeue=100,
        )

        if n1 or n2:
            logger.warning(
                "reaper_requeued",
                extra={"event": "queue.reaper_requeued", "scrape": n1, "extract": n2},
            )

    except Exception:
        logger.exception("reaper_error", extra={"event": "queue.reaper_error"})

    time.sleep(POLL_SEC)
