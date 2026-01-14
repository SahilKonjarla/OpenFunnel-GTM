import time
from redis import Redis
from app.core.config import settings
from app.queue.redis_queue import reserve_task, ack_task, fail_task
from app.db.session import get_redis, SessionLocal
from app.core.logging import init_logging, get_logger
from app.core.request_context import set_trace_id, clear_trace_id
from app.services.scraping.providers import fetch_url
from app.services.storage.job_store import store_raw_response

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

    db = SessionLocal()
    try:
        url = (task.payload or {}).get("url")
        if not url:
            raise ValueError("missing payload.url for scrape task")

        http_status, content_type, headers_json, body_text = fetch_url(url, settings.http_timeout_sec)

        store_raw_response(
            db,
            job_posting_id=task.job_posting_id,
            url=url,
            http_status=http_status,
            content_type=content_type,
            headers_json=headers_json,
            body_text=body_text,
        )
        db.commit()

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
        db.rollback()
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
        db.close()
        clear_trace_id()
        time.sleep(0.01)
