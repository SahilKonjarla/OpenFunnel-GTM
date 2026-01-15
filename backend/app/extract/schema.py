from pydantic import BaseModel, Field

class ExtractionLLM(BaseModel):
    summary: str
    role_function: str
    seniority: str | None = None
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    skills: list[str] = Field(default_factory=list)
