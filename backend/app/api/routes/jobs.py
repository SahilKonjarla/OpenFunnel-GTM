from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from app.db.models import JobPosting
from app.db.session import get_db

# Router for search/query endpoints over job postings.
router = APIRouter()

@router.get("/search")
def search(
    # Free-text search query (currently applied to job title).
    q: str | None = None,
    # Filter by company name (substring match, case-insensitive).
    company: str | None = None,
    # Filter by city (substring match, case-insensitive).
    city: str | None = None,
    # Minimum acceptable salary (compared against salary_max).
    min_salary: int | None = None,
    # Maximum acceptable salary (compared against salary_min).
    max_salary: int | None = None,
    # Filter by seniority level (exact match).
    seniority: str | None = None,
    # Filter by role function/category (exact match).
    role_function: str | None = None,
    # Filter by skill keyword (applied in Python post-query).
    skill: str | None = None,
    # Pagination: cap result size to avoid huge payloads / DB load.
    limit: int = Query(default=50, le=200),
    # Pagination: number of rows to skip.
    offset: int = 0,
    # Inject a SQLAlchemy session (request-scoped).
    db: Session = Depends(get_db),
) -> dict:
    # Build SQL filters dynamically based on which query params were provided.
    filters = []

    if company:
        # Case-insensitive substring match for company name.
        filters.append(JobPosting.company_name.ilike(f"%{company}%"))
    if city:
        # Case-insensitive substring match for city.
        filters.append(JobPosting.location_city.ilike(f"%{city}%"))
    if seniority:
        # Exact match on seniority (e.g., "junior", "mid", "senior").
        filters.append(JobPosting.seniority == seniority)
    if role_function:
        # Exact match on role function (e.g., "backend", "ml", "infra").
        filters.append(JobPosting.role_function == role_function)
    if min_salary is not None:
        # Only include postings where salary_max exists and is >= min_salary.
        filters.append(JobPosting.salary_max.isnot(None))
        filters.append(JobPosting.salary_max >= min_salary)
    if max_salary is not None:
        # Only include postings where salary_min exists and is <= max_salary.
        filters.append(JobPosting.salary_min.isnot(None))
        filters.append(JobPosting.salary_min <= max_salary)
    if q:
        # Free-text title match (case-insensitive substring).
        filters.append(JobPosting.title.ilike(f"%{q}%"))

    # Construct the SQLAlchemy statement.
    # If no filters are provided, we select all postings.
    stmt = select(JobPosting).where(and_(*filters)) if filters else select(JobPosting)

    # Sort newest-first and apply pagination.
    stmt = stmt.order_by(JobPosting.discovered_at.desc()).limit(limit).offset(offset)

    # Execute query and materialize results.
    rows = db.execute(stmt).scalars().all()

    # Optional skill filtering:
    # We apply this in Python because `skills` is a JSON/list column,
    # and filtering it in SQL can vary depending on DB type + schema.
    if skill:
        s = skill.lower()
        rows = [
            r
            for r in rows
            if isinstance(r.skills, list) and s in [x.lower() for x in r.skills]
        ]

    # Return a lightweight JSON response (explicitly serializing UUIDs, etc.)
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
