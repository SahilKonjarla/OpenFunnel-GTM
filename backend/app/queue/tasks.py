from pydantic import BaseModel, Field
from typing import Literal, Any
from uuid import uuid4
from datetime import datetime as dt

class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    trace_id: str
    run_id: str
    job_posting_id: str
    task_type: Literal["scrape", "extract"]
    attempt: int = 0
    created_at: str = Field(default_factory=lambda: dt.utcnow().isoformat())
    payload: dict[str, Any]