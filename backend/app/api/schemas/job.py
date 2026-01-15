from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class JobPostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    external_id: Optional[str] = None
    canonical_url: Optional[str] = None
    company_name: str
    title: Optional[str] = None
    location_raw: Optional[str] = None

    status: str
    discovered_at: datetime
    fetched_at: Optional[datetime] = None
    extracted_at: Optional[datetime] = None


class ExtractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_posting_id: UUID
    extracted_at: datetime

    summary: Optional[str] = None
    seniority: Optional[str] = None
    remote_flag: Optional[bool] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None

    hiring_function: Optional[str] = None

    location_city: Optional[str] = None
    location_region: Optional[str] = None
    location_country: Optional[str] = None

    extra_json: Optional[dict[str, Any]] = None


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_name: str
