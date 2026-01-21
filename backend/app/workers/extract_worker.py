from __future__ import annotations
import datetime as dt, time
from app.core.logging import init_logging, get_logger
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import JobPosting
from app.db.redis_client import get_redis
from app.queue.redis_queue import lease_batch, ack, fail_and_maybe_requeue
from app.llm.ollama_client import chat as ollama_chat
from app.llm.high_tier import chat as high_tier_chat
from app.extract.prompts import small_model_prompt, high_tier_prompt
from app.extract.parse import extract_json
from app.extract.schema import ExtractionLLM
from app.normalize.skills import canonicalize

init_logging("worker_extract")
logger = get_logger(__name__)
r = get_redis()

def needs_escalation(parsed: ExtractionLLM) -> bool:
    if not parsed.role_function or parsed.role_function == "other":
        return True
    if len(parsed.skills) < 2:
        return True
    return False

while True:
    tasks = lease_batch(r, "extract", batch_size=settings.extract_batch_size, visibility_timeout_sec=settings.visibility_timeout_sec)
    if not tasks:
        time.sleep(0.5); continue

    for t in tasks:
        db = SessionLocal()
        try:
            jid = t.payload["job_posting_id"]
            jp = db.query(JobPosting).filter(JobPosting.id==jid).first()
            if not jp or not jp.description_text:
                ack(r, "extract", t); continue

            raw1 = ollama_chat(small_model_prompt(jp.description_text))
            data1 = extract_json(raw1)
            parsed1 = ExtractionLLM.model_validate(data1)

            parsed = parsed1
            if (settings.openai_api_key or settings.anthropic_api_key) and needs_escalation(parsed1):
                print("high tier")
                raw2 = high_tier_chat(high_tier_prompt(jp.description_text))
                data2 = extract_json(raw2)
                parsed = ExtractionLLM.model_validate(data2)

            skills = canonicalize(parsed.skills)
            jp.summary = parsed.summary
            jp.role_function = parsed.role_function
            jp.seniority = parsed.seniority
            jp.location_city = parsed.location_city
            jp.location_state = parsed.location_state
            jp.location_country = parsed.location_country
            jp.salary_min = parsed.salary_min
            jp.salary_max = parsed.salary_max
            jp.salary_currency = parsed.salary_currency
            jp.skills = skills
            jp.technologies = skills[:12]
            jp.status = "extracted"
            jp.extracted_at = dt.datetime.now(dt.timezone.utc)
            db.commit()

            ack(r, "extract", t)

        except Exception:
            logger.exception("extract_error", extra={"task_id": t.id})
            fail_and_maybe_requeue(r, "extract", t)
        finally:
            db.close()
