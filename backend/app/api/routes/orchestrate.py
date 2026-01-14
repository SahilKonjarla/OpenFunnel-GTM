from fastapi import APIRouter, Depends
from redis import Redis
from uuid import uuid4
from sqlalchemy.orm import Session
from app.queue.redis_queue import enqueue_task
from app.core.config import settings
from app.core.request_context import set_trace_id, clear_trace_id
from app.queue.tasks import Task
from app.db.session import get_redis, get_db
from app.core.logging import get_logger
from app.services.storage.run_store import create_run
from app.services.storage.job_store import upsert_job_posting
from app.services.scraping.providers import greenhouse_jobs_list, lever_jobs_list

orchestrate_router = APIRouter()
logger = get_logger(__name__)

def _seed_discovered_jobs(db: Session, source: str, n: int) -> tuple[list[str], dict[str, str]]:
    """
    Returns (job_posting_ids, url_by_job_posting_id)
    """
    if source == "greenhouse":
        jobs = greenhouse_jobs_list(settings.greenhouse_board, n, settings.http_timeout_sec)
        company = settings.greenhouse_board
        items = []
        for j in jobs:
            items.append(
                {
                    "external_id": str(j.get("id")),
                    "canonical_url": j.get("absolute_url"),
                    "title": j.get("title"),
                    "location_raw": (j.get("location") or {}).get("name"),
                    "company_name": company,
                }
            )
    elif source == "lever":
        jobs = lever_jobs_list(settings.lever_company, n, settings.http_timeout_sec)
        company = settings.lever_company
        items = []
        for j in jobs:
            cats = j.get("categories") if isinstance(j.get("categories"), dict) else {}
            items.append(
                {
                    "external_id": str(j.get("id") or j.get("postingId") or j.get("hostedUrl")),
                    "canonical_url": j.get("hostedUrl"),
                    "title": j.get("text"),
                    "location_raw": cats.get("location"),
                    "company_name": company,
                }
            )
    else:
        raise ValueError(f"unknown source: {source}")

    job_ids: list[str] = []
    url_by_id: dict[str, str] = {}

    for it in items:
        jp = upsert_job_posting(
            db,
            source=source,
            external_id=it["external_id"],
            canonical_url=it["canonical_url"],
            company_name=it["company_name"],
            title=it.get("title"),
            location_raw=it.get("location_raw"),
        )
        jid = str(jp.id)
        job_ids.append(jid)
        url_by_id[jid] = it["canonical_url"]

    return job_ids, url_by_id

@orchestrate_router.post("/run/all", tags=["orchestrate"])
def run_all(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        source = "greenhouse"  # switch to "lever" if you want
        run = create_run(db, source=source, status="running", notes="run_all real seed")

        job_ids, url_by_id = _seed_discovered_jobs(db, source, settings.seed_job_limit)
        db.commit()

        for jid in job_ids:
            enqueue_task(
                redis,
                Task(
                    trace_id=trace_id,
                    run_id=str(run.id),
                    job_posting_id=jid,
                    task_type="scrape",
                    payload={"url": url_by_id[jid]},
                ),
            )
            enqueue_task(
                redis,
                Task(
                    trace_id=trace_id,
                    run_id=str(run.id),
                    job_posting_id=jid,
                    task_type="extract",
                    payload={},
                ),
            )

        logger.info(
            "run_all_enqueued",
            extra={"event": "api.run_all_enqueued", "run_id": str(run.id), "count": len(job_ids) * 2},
        )
        return {"status": "enqueued", "trace_id": trace_id, "run_id": str(run.id), "job_count": len(job_ids)}
    finally:
        clear_trace_id()


@orchestrate_router.post("/run/scrape", tags=["orchestrate"])
def run_scrape(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        source = "greenhouse"  # switch to "lever" if you want
        run = create_run(db, source=source, status="running", notes="run_scrape real seed")

        job_ids, url_by_id = _seed_discovered_jobs(db, source, settings.seed_job_limit)
        db.commit()

        for jid in job_ids:
            enqueue_task(
                redis,
                Task(
                    trace_id=trace_id,
                    run_id=str(run.id),
                    job_posting_id=jid,
                    task_type="scrape",
                    payload={"url": url_by_id[jid]},
                ),
            )

        return {"status": "enqueued", "trace_id": trace_id, "run_id": str(run.id), "job_count": len(job_ids)}
    finally:
        clear_trace_id()


@orchestrate_router.post("/run/extract", tags=["orchestrate"])
def run_extract(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        source = "greenhouse"  # switch to "lever" if you want
        run = create_run(db, source=source, status="running", notes="run_extract real seed")

        job_ids, _ = _seed_discovered_jobs(db, source, settings.seed_job_limit)
        db.commit()

        for jid in job_ids:
            enqueue_task(
                redis,
                Task(
                    trace_id=trace_id,
                    run_id=str(run.id),
                    job_posting_id=jid,
                    task_type="extract",
                    payload={},
                ),
            )

        return {"status": "enqueued", "trace_id": trace_id, "run_id": str(run.id), "job_count": len(job_ids)}
    finally:
        clear_trace_id()
