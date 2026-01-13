from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.storage.job_store import upsert_job_posting, store_raw_response, store_extraction, upsert_skills_and_links

debug_router = APIRouter(prefix="/debug", tags=["debug"])
logger = get_logger(__name__)

@debug_router.post("/seed_one")
def seed_one(db: Session = Depends(get_db)):
    jp = upsert_job_posting(
        db,
        source="greenhouse",
        external_id="demo-1",
        canonical_url="https://example.com/job/demo-1",
        company_name="DemoCo",
        title="Software Engineer",
        location_raw="San Francisco, CA",
    )
    store_raw_response(
        db,
        job_posting_id=jp.id,
        url="https://example.com/job/demo-1",
        http_status=200,
        content_type="text/html",
        headers_json={"x-demo": "1"},
        body_text="<html>hello</html>",
    )
    ext = store_extraction(
        db,
        job_posting_id=jp.id,
        extraction_fields={
            "summary": "demo summary",
            "seniority": "mid",
            "remote_flag": False,
            "salary_min": 120000,
            "salary_max": 160000,
            "salary_currency": "USD",
        },
        extra_json={"source": "seed"},
    )
    upsert_skills_and_links(db, job_posting_id=jp.id, canonical_skill_names=["python", "fastapi", "redis"])
    db.commit()

    logger.info("seed_one_ok", extra={"event": "debug.seed_one_ok", "job_posting_id": str(jp.id)})
    return {"job_posting_id": str(jp.id), "extraction_id": str(ext.id)}
