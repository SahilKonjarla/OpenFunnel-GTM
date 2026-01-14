import time
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.queue.redis_queue import reserve_task, ack_task, fail_task
from app.db.session import get_redis, SessionLocal
from app.core.logging import init_logging, get_logger
from app.core.request_context import set_trace_id, clear_trace_id
from app.db.models import RawResponse
from app.services.extraction.ollama_client import ollama_chat
from app.services.extraction.json_parse import parse_json
from app.services.extraction.prompting import build_extraction_prompt
from app.services.storage.job_store import store_extraction, upsert_skills_and_links

init_logging("worker_extractor")
logger = get_logger(__name__)
r: Redis = get_redis()

while True:
    task = reserve_task(r, task_type="extract", block_seconds=5)
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
        rr = db.execute(
            select(RawResponse)
            .where(RawResponse.job_posting_id == task.job_posting_id)
            .order_by(RawResponse.fetched_at.desc())
            .limit(1)
        ).scalars().first()

        if not rr:
            raise ValueError("No raw_response found for job_posting_id; scrape must run first")

        prompt = build_extraction_prompt(html_text=rr.body_text[:12000])  # cap
        out = ollama_chat(
            base_url=settings.ollama_url,
            model=settings.ollama_model,
            prompt=prompt,
            timeout_sec=90,
        )
        data = parse_json(out)

        skills = data.pop("skills", []) or []
        extraction_fields = data

        store_extraction(
            db,
            job_posting_id=task.job_posting_id,
            extraction_fields=extraction_fields,
            extra_json={"model_output_raw": out[:4000]},  # keep short
        )
        upsert_skills_and_links(db, job_posting_id=task.job_posting_id, canonical_skill_names=skills)

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