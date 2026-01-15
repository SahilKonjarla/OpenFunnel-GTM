from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class ExtractionLLM(BaseModel):
    summary: Optional[str] = None
    seniority: Optional[str] = None
    remote_flag: Optional[bool] = None

    salary_min: Optional[float] = Field(default=None, ge=0)
    salary_max: Optional[float] = Field(default=None, ge=0)
    salary_currency: Optional[str] = None

    hiring_function: Optional[str] = None

    location_city: Optional[str] = None
    location_region: Optional[str] = None
    location_country: Optional[str] = None

    skills: list[str] = Field(default_factory=list)
