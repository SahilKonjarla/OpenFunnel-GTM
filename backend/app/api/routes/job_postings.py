from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.db.models import JobPosting, Extraction, Skill, JobSkill
from app.db.session import get_db
from app.api.schemas.job import JobPostingOut, ExtractionOut, SkillOut

router = APIRouter(prefix="", tags=["read"])
logger = get_logger(__name__)


@router.get("/job_postings", response_model=list[JobPostingOut])
def list_job_postings(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(JobPosting).order_by(JobPosting.discovered_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(JobPosting.status == status)

    rows = db.execute(stmt).scalars().all()
    return rows


@router.get("/job_postings/{job_posting_id}", response_model=JobPostingOut)
def get_job_posting(job_posting_id: str, db: Session = Depends(get_db)):
    jp = db.get(JobPosting, job_posting_id)
    if not jp:
        raise HTTPException(status_code=404, detail="job_posting not found")
    return jp


@router.get("/job_postings/{job_posting_id}/extraction", response_model=ExtractionOut)
def get_extraction(job_posting_id: str, db: Session = Depends(get_db)):
    ext = db.execute(
        select(Extraction).where(Extraction.job_posting_id == job_posting_id)
    ).scalars().first()
    if not ext:
        raise HTTPException(status_code=404, detail="extraction not found")
    return ext


@router.get("/job_postings/{job_posting_id}/skills", response_model=list[SkillOut])
def get_skills(job_posting_id: str, db: Session = Depends(get_db)):
    skill_rows = db.execute(
        select(Skill)
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .where(JobSkill.job_posting_id == job_posting_id)
        .order_by(Skill.canonical_name.asc())
    ).scalars().all()
    return skill_rows
