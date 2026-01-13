from fastapi import APIRouter, Depends
from redis import Redis
from uuid import uuid4
from sqlalchemy.orm import Session
from app.queue.redis_queue import enqueue_task
from app.core.request_context import set_trace_id, clear_trace_id
from app.queue.tasks import Task
from app.db.session import get_redis, get_db
from app.core.logging import get_logger
from app.services.storage.run_store import create_run
from app.services.storage.job_store import upsert_job_posting

orchestrate_router = APIRouter()
logger = get_logger(__name__)

def _seed_discovered_jobs(db: Session, source: str, n: int) -> list[str]:
    ids: list[str] = []
    for i in range(n):
        jp = upsert_job_posting(
            db,
            source=source,
            external_id=f"seed-{i}",
            canonical_url=f"https://example.com/{source}/seed-{i}",
            company_name="SeedCo",
            title=f"Seed Role {i}",
            location_raw="Remote",
        )
        ids.append(str(jp.id))
    return ids

@orchestrate_router.post("/run/all", tags=["orchestrate"])
def run_all(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        run = create_run(db, source="greenhouse", status="running", notes="run_all seed")
        job_ids = _seed_discovered_jobs(db, "greenhouse", 5)
        db.commit()

        for jid in job_ids:
            enqueue_task(redis, Task(trace_id=trace_id, run_id=str(run.id), job_posting_id=jid, task_type="scrape", payload={}))
            enqueue_task(redis, Task(trace_id=trace_id, run_id=str(run.id), job_posting_id=jid, task_type="extract", payload={}))

        logger.info("run_all_enqueued", extra={"event": "api.run_all_enqueued", "run_id": str(run.id), "count": len(job_ids) * 2})
        return {"status": "enqueued", "trace_id": trace_id, "run_id": str(run.id), "job_count": len(job_ids)}
    finally:
        clear_trace_id()

@orchestrate_router.post("/run/scrape", tags=["orchestrate"])
def run_scrape(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        run = create_run(db, source="greenhouse", status="running", notes="run_scrape seed")
        job_ids = _seed_discovered_jobs(db, "greenhouse", 5)
        db.commit()

        for jid in job_ids:
            enqueue_task(redis, Task(trace_id=trace_id, run_id=str(run.id), job_posting_id=jid, task_type="scrape", payload={}))

        return {"status": "enqueued", "trace_id": trace_id, "run_id": str(run.id), "job_count": len(job_ids)}
    finally:
        clear_trace_id()

@orchestrate_router.post("/run/extract", tags=["orchestrate"])
def run_extract(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    try:
        run = create_run(db, source="greenhouse", status="running", notes="run_extract seed")
        job_ids = _seed_discovered_jobs(db, "greenhouse", 5)
        db.commit()

        for jid in job_ids:
            enqueue_task(redis, Task(trace_id=trace_id, run_id=str(run.id), job_posting_id=jid, task_type="extract", payload={}))

        return {"status": "enqueued", "trace_id": trace_id, "run_id": str(run.id), "job_count": len(job_ids)}
    finally:
        clear_trace_id()
