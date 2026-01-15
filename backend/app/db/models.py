import datetime as dt
import uuid
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Run(Base):
    __tablename__ = "runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    note = Column(Text, nullable=True)

class RawResponse(Base):
    __tablename__ = "raw_responses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True, index=True)
    source = Column(String(32), nullable=False)
    url = Column(Text, nullable=False)
    url_hash = Column(String(64), nullable=False, index=True)
    status_code = Column(Integer, nullable=False)
    content_type = Column(String(128), nullable=True)
    body = Column(JSON, nullable=True)
    body_text = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

class JobPosting(Base):
    __tablename__ = "job_postings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True, index=True)

    source = Column(String(32), nullable=False)
    external_id = Column(String(128), nullable=True, index=True)
    company_name = Column(String(256), nullable=False, index=True)
    title = Column(String(512), nullable=True, index=True)

    location_raw = Column(Text, nullable=True)
    location_city = Column(String(128), nullable=True, index=True)
    location_state = Column(String(64), nullable=True, index=True)
    location_country = Column(String(64), nullable=True, index=True)

    salary_min = Column(Integer, nullable=True, index=True)
    salary_max = Column(Integer, nullable=True, index=True)
    salary_currency = Column(String(16), nullable=True)

    seniority = Column(String(64), nullable=True, index=True)
    role_function = Column(String(128), nullable=True, index=True)
    summary = Column(Text, nullable=True)

    skills = Column(JSON, nullable=True)
    technologies = Column(JSON, nullable=True)

    description_text = Column(Text, nullable=True)
    canonical_url = Column(Text, nullable=True, index=True)

    status = Column(String(24), nullable=False, default="discovered", index=True)

    discovered_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    extracted_at = Column(DateTime(timezone=True), nullable=True)

Index("ix_job_postings_company_title", JobPosting.company_name, JobPosting.title)
