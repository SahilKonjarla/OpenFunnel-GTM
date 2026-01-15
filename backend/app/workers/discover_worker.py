import time
from redis import Redis
from sqlalchemy.orm import Session
from app.core.config import settings
from app.queue.redis_queue import reserve_task, ack_task, fail_task, enqueue_task
from app.db.session import get_redis, SessionLocal
from app.core.logging import init_logging, get_logger
from app.core.request_context import set_trace_id, clear_trace_id
from app.queue.tasks import Task
from app.services.storage.job_store import upsert_job_posting
from app.services.scraping.providers import greenhouse_jobs_list, lever_jobs_list, lever_jobs_page

init_logging("worker_discover")
logger = get_logger(__name__)
r: Redis = get_redis()


def _discover_greenhouse(board: str, limit: int) -> list[dict]:
    jobs = greenhouse_jobs_list(board, limit, settings.http_timeout_sec)
    items = []
    for j in jobs:
        items.append(
            {
                "source": "greenhouse",
                "external_id": str(j.get("id")),
                "canonical_url": j.get("absolute_url"),
                "title": j.get("title"),
                "location_raw": (j.get("location") or {}).get("name"),
                "company_name": board,
            }
        )
    return items


def _discover_lever(company: str, limit: int) -> list[dict]:
    # If limit is small, your existing lever_jobs_list is fine.
    # If limit is large, paginate using lever_jobs_page.
    items = []

    page_limit = min(getattr(settings, "lever_page_limit", 100), 100)

    if limit <= page_limit:
        jobs = lever_jobs_list(company, limit, settings.http_timeout_sec)
        for j in jobs:
            cats = j.get("categories") if isinstance(j.get("categories"), dict) else {}
            items.append(
                {
                    "source": "lever",
                    "external_id": str(j.get("id") or j.get("postingId") or j.get("hostedUrl")),
                    "canonical_url": j.get("hostedUrl"),
                    "title": j.get("text"),
                    "location_raw": cats.get("location"),
                    "company_name": company,
                }
            )
        return items

    # paginate
    offset = None
    while len(items) < limit:
        per_page = min(page_limit, limit - len(items))
        jobs, next_offset, has_next = lever_jobs_page(company, per_page, settings.http_timeout_sec, offset=offset)

        for j in jobs:
            cats = j.get("categories") if isinstance(j.get("categories"), dict) else {}
            items.append(
                {
                    "source": "lever",
                    "external_id": str(j.get("id") or j.get("postingId") or j.get("hostedUrl")),
                    "canonical_url": j.get("hostedUrl"),
                    "title": j.get("text"),
                    "location_raw": cats.get("location"),
                    "company_name": company,
                }
            )

        if not has_next or not next_offset:
            break
        offset = next_offset

    return items[:limit]


while True:
    task = reserve_task(r, task_type="discover", block_seconds=5)
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
            "job_posting_id": task.job_posting_id,  # will be None for discover
            "attempt": task.attempt,
        },
    )

    db: Session = SessionLocal()
    try:
        payload = task.payload or {}
        source = payload.get("source")  # "greenhouse" | "lever"
        limit = int(payload.get("limit") or getattr(settings, "discovery_per_target_limit", 500))

        if source == "greenhouse":
            board = payload.get("board") or settings.greenhouse_board
            items = _discover_greenhouse(board, limit)
        elif source == "lever":
            company = payload.get("company") or settings.lever_company
            items = _discover_lever(company, limit)
        else:
            raise ValueError(f"unknown discover source: {source}")

        enqueued_jobs = 0

        for it in items:
            # NOTE: upsert_job_posting now returns (jp, created_or_changed)
            jp, created_or_changed = upsert_job_posting(
                db,
                source=it["source"],
                external_id=it["external_id"],
                canonical_url=it["canonical_url"],
                company_name=it["company_name"],
                title=it.get("title"),
                location_raw=it.get("location_raw"),
            )

            if not it.get("canonical_url"):
                continue

            # Only enqueue downstream if this was new/meaningfully updated.
            # This prevents re-running discovery from spamming the queue.
            if created_or_changed:
                jid = str(jp.id)

                enqueue_task(
                    r,
                    Task(
                        trace_id=task.trace_id,
                        run_id=task.run_id,
                        job_posting_id=jid,
                        task_type="scrape",
                        payload={"url": it["canonical_url"]},
                    ),
                )
                enqueue_task(
                    r,
                    Task(
                        trace_id=task.trace_id,
                        run_id=task.run_id,
                        job_posting_id=jid,
                        task_type="extract",
                        payload={},
                    ),
                )
                enqueued_jobs += 1

        db.commit()
        ack_task(r, task)

        logger.info(
            "task_ok",
            extra={
                "event": "task_ok",
                "task_id": task.task_id,
                "task_type": task.task_type,
                "run_id": task.run_id,
                "discovered": len(items),
                "enqueued_jobs": enqueued_jobs,
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
