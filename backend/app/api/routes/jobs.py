from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.db.session import get_db
from app.db.models import JobPosting

router = APIRouter()

@router.get("/search")
def search(
    q: str | None = None,
    company: str | None = None,
    city: str | None = None,
    min_salary: int | None = None,
    max_salary: int | None = None,
    seniority: str | None = None,
    role_function: str | None = None,
    skill: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    filters = []
    if company:
        filters.append(JobPosting.company_name.ilike(f"%{company}%"))
    if city:
        filters.append(JobPosting.location_city.ilike(f"%{city}%"))
    if seniority:
        filters.append(JobPosting.seniority == seniority)
    if role_function:
        filters.append(JobPosting.role_function == role_function)
    if min_salary is not None:
        filters.append(JobPosting.salary_max.isnot(None))
        filters.append(JobPosting.salary_max >= min_salary)
    if max_salary is not None:
        filters.append(JobPosting.salary_min.isnot(None))
        filters.append(JobPosting.salary_min <= max_salary)
    if q:
        filters.append(JobPosting.title.ilike(f"%{q}%"))

    stmt = select(JobPosting).where(and_(*filters)) if filters else select(JobPosting)
    stmt = stmt.order_by(JobPosting.discovered_at.desc()).limit(limit).offset(offset)
    rows = db.execute(stmt).scalars().all()

    if skill:
        s = skill.lower()
        rows = [r for r in rows if isinstance(r.skills, list) and s in [x.lower() for x in r.skills]]

    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "company_name": r.company_name,
                "title": r.title,
                "location_raw": r.location_raw,
                "location_city": r.location_city,
                "salary_min": r.salary_min,
                "salary_max": r.salary_max,
                "seniority": r.seniority,
                "role_function": r.role_function,
                "skills": r.skills,
                "summary": r.summary,
                "canonical_url": r.canonical_url,
                "status": r.status,
                "description_text": r.description_text,
            }
            for r in rows
        ],
    }
