from __future__ import annotations
import datetime as dt, time
from sqlalchemy.orm import Session
from app.core.logging import init_logging, get_logger
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import RawResponse, JobPosting
from app.db.redis_client import get_redis
from app.queue.redis_queue import lease_batch, ack, fail_and_maybe_requeue, enqueue
from app.scraper.greenhouse import fetch_board, fetch_job, job_url
from app.utils.hashing import sha256_hex
from app.utils.raw_store import store_json

init_logging("worker_scrape")
logger = get_logger(__name__)
r = get_redis()

def upsert_job_stub(db: Session, company: str, job_id: int, title: str | None, location: str | None, url: str):
    existing = db.query(JobPosting).filter(
        JobPosting.source=="greenhouse",
        JobPosting.external_id==str(job_id),
        JobPosting.company_name==company
    ).first()
    if existing:
        return existing
    jp = JobPosting(
        source="greenhouse",
        external_id=str(job_id),
        company_name=company,
        title=title,
        location_raw=location,
        canonical_url=url,
        status="discovered",
        discovered_at=dt.datetime.now(dt.timezone.utc),
    )
    db.add(jp); db.commit()
    return jp

while True:
    tasks = lease_batch(r, "discover", batch_size=16, visibility_timeout_sec=settings.visibility_timeout_sec)
    if not tasks:
        tasks = lease_batch(r, "scrape", batch_size=32, visibility_timeout_sec=settings.visibility_timeout_sec)
        if not tasks:
            time.sleep(0.5); continue

    for t in tasks:
        db = SessionLocal()
        try:
            if t.type == "discover":
                company = t.payload["company"]
                status, data, headers, ctype = fetch_board(company)
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
                url_hash = sha256_hex(url)
                db.add(RawResponse(
                    source="greenhouse", url=url, url_hash=url_hash,
                    status_code=status, content_type=ctype, body=data,
                    fetched_at=dt.datetime.now(dt.timezone.utc),
                ))
                db.commit()
                if data and "jobs" in data:
                    for job in data["jobs"]:
                        jid = job.get("id")
                        title = job.get("title")
                        loc = (job.get("location") or {}).get("name")
                        upsert_job_stub(db, company, jid, title, loc, job_url(company, jid))
                        enqueue(r, "scrape", {"company": company, "job_id": jid})
                ack(r, "discover", t)

            elif t.type == "scrape":
                company = t.payload["company"]
                job_id = int(t.payload["job_id"])
                status, data, headers, ctype = fetch_job(company, job_id)
                url = job_url(company, job_id)
                url_hash = sha256_hex(url)
                db.add(RawResponse(
                    source="greenhouse", url=url, url_hash=url_hash,
                    status_code=status, content_type=ctype, body=data,
                    fetched_at=dt.datetime.now(dt.timezone.utc),
                ))
                jp = db.query(JobPosting).filter(
                    JobPosting.source=="greenhouse",
                    JobPosting.external_id==str(job_id),
                    JobPosting.company_name==company,
                ).first()
                if jp and data:
                    jp.description_text = data.get("content") or ""
                    jp.title = data.get("title") or jp.title
                    loc = (data.get("location") or {}).get("name")
                    jp.location_raw = loc or jp.location_raw
                    jp.canonical_url = data.get("absolute_url") or jp.canonical_url
                    jp.status = "fetched"
                    jp.fetched_at = dt.datetime.now(dt.timezone.utc)
                    enqueue(r, "extract", {"job_posting_id": str(jp.id)})
                db.commit()
                if data:
                    store_json(url_hash, data)
                ack(r, "scrape", t)

        except Exception:
            logger.exception("task_error", extra={"task_type": t.type, "task_id": t.id})
            fail_and_maybe_requeue(r, t.type, t)
        finally:
            db.close()
