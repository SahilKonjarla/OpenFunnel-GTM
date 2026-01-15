from __future__ import annotations
import hashlib
from datetime import datetime as dt
from typing import Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import JobPosting, RawResponse, Extraction, Skill, JobSkill

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def upsert_job_posting(
    db: Session,
    *,
    source: str,
    company_name: str,
    external_id: Optional[str] = None,
    canonical_url: Optional[str] = None,
    title: Optional[str] = None,
    location_raw: Optional[str] = None,
) -> Tuple[JobPosting, bool]:
    url_hash: Optional[str] = None
    if not external_id and canonical_url:
        url_hash = _sha256(canonical_url)

    # find existing
    stmt = None
    if external_id:
        stmt = select(JobPosting).where(JobPosting.source == source, JobPosting.external_id == external_id)
    elif url_hash:
        stmt = select(JobPosting).where(JobPosting.source == source, JobPosting.canonical_url_hash == url_hash)

    existing: Optional[JobPosting] = db.execute(stmt).scalars().first() if stmt is not None else None

    if existing:
        changed = False
        # only fill fields if missing
        if title and not existing.title:
            existing.title = title
            changed = True
        if location_raw and not existing.location_raw:
            existing.location_raw = location_raw
            changed = True
        if canonical_url and not existing.canonical_url:
            existing.canonical_url = canonical_url
            changed = True
        if url_hash and not existing.canonical_url_hash:
            existing.canonical_url_hash = url_hash
            changed = True
        if company_name and not existing.company_name:
            existing.company_name = company_name
            changed = True
        return existing, changed

    jp = JobPosting(
        source=source,
        external_id=external_id,
        canonical_url=canonical_url,
        canonical_url_hash=url_hash,
        company_name=company_name,
        title=title,
        location_raw=location_raw,
        status="discovered",
        discovered_at=dt.utcnow(),
    )
    db.add(jp)
    db.flush()
    return jp, True

def store_raw_response(
    db: Session,
    *,
    job_posting_id,
    url: str,
    http_status: Optional[int],
    content_type: Optional[str],
    headers_json: Optional[dict[str, Any]],
    body_text: str,
) -> RawResponse:
    checksum = _sha256(body_text)

    rr = RawResponse(
        job_posting_id=job_posting_id,
        url=url,
        http_status=http_status,
        content_type=content_type,
        headers_json=headers_json,
        body_text=body_text,
        checksum=checksum,
        fetched_at=dt.utcnow(),
    )
    db.add(rr)

    # update job posting lifecycle
    jp = db.get(JobPosting, job_posting_id)
    if jp:
        jp.status = "fetched"
        jp.fetched_at = dt.utcnow()

    db.flush()
    return rr


def store_extraction(
    db: Session,
    *,
    job_posting_id,
    extraction_fields: dict[str, Any],
    extra_json: Optional[dict[str, Any]] = None,
) -> Extraction:
    # upsert extraction (1 per job_posting)
    existing = db.execute(
        select(Extraction).where(Extraction.job_posting_id == job_posting_id)
    ).scalars().first()

    if existing:
        ext = existing
    else:
        ext = Extraction(job_posting_id=job_posting_id)
        db.add(ext)

    # set modeled fields if present
    for k, v in extraction_fields.items():
        if hasattr(ext, k):
            setattr(ext, k, v)

    if extra_json is not None:
        ext.extra_json = extra_json

    ext.extracted_at = dt.utcnow()

    # update job posting lifecycle
    jp = db.get(JobPosting, job_posting_id)
    if jp:
        jp.status = "extracted"
        jp.extracted_at = dt.utcnow()

    db.flush()
    return ext

def upsert_skills_and_links(
    db: Session,
    *,
    job_posting_id,
    canonical_skill_names: list[str],
) -> None:
    cleaned = sorted({s.strip().lower() for s in canonical_skill_names if s and s.strip()})
    if not cleaned:
        return

    existing_skills = db.execute(select(Skill).where(Skill.canonical_name.in_(cleaned))).scalars().all()
    existing_map = {s.canonical_name: s for s in existing_skills}

    for name in cleaned:
        if name not in existing_map:
            skill = Skill(canonical_name=name)
            db.add(skill)
            db.flush()
            existing_map[name] = skill

        # link (ignore duplicates by checking first)
        already = db.execute(
            select(JobSkill).where(JobSkill.job_posting_id == job_posting_id, JobSkill.skill_id == existing_map[name].id)
        ).scalars().first()

        if not already:
            db.add(JobSkill(job_posting_id=job_posting_id, skill_id=existing_map[name].id))

    db.flush()
