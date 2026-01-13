from __future__ import annotations
from datetime import datetime as dt
from uuid import uuid4
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

def _uuid() -> str:
    return str(uuid4())

class Run(Base):
    __tablename__ = "runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    created_at = Column(DateTime(timezone=True), nullable=False, default=dt.utcnow)
    source = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False, default="running")
    notes = Column(Text, nullable=True)

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    source = Column(String(32), nullable=False)  # greenhouse|lever|other
    external_id = Column(String(128), nullable=True)
    canonical_url = Column(Text, nullable=True)
    canonical_url_hash = Column(String(64), nullable=True)

    company_name = Column(String(256), nullable=False)
    title = Column(String(512), nullable=True)

    location_raw = Column(String(512), nullable=True)
    status = Column(String(16), nullable=False, default="discovered")

    discovered_at = Column(DateTime(timezone=True), nullable=False, default=dt.utcnow())
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    extracted_at = Column(DateTime(timezone=True), nullable=True)

    raw_responses = relationship("RawResponse", back_populates="job_posting", cascade="all, delete-orphan")
    extraction = relationship("Extraction", back_populates="job_posting", uselist=False, cascade="all, delete-orphan")
    job_skills = relationship("JobSkill", back_populates="job_posting", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_job_source_external_id"),
        UniqueConstraint("source", "canonical_url_hash", name="uq_job_source_url_hash"),
        Index("ix_job_source_company", "source", "company_name"),
        Index("ix_job_title", "title"),
        Index("ix_job_location_raw", "location_raw"),
        Index("ix_job_status", "status"),
    )

class RawResponse(Base):
    __tablename__ = "raw_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)

    fetched_at = Column(DateTime(timezone=True), nullable=False, default=dt.utcnow())
    url = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    content_type = Column(String(128), nullable=True)

    headers_json = Column(JSONB, nullable=True)
    body_text = Column(Text, nullable=True)
    checksum = Column(String(64), nullable=True)

    job_posting = relationship("JobPosting", back_populates="raw_responses")

    __table_args__ = (
        Index("ix_raw_job_posting_id", "job_posting_id"),
        Index("ix_raw_checksum", "checksum"),
    )


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, unique=True)

    extracted_at = Column(DateTime(timezone=True), nullable=False, default=dt.utcnow())

    summary = Column(Text, nullable=True)
    hiring_function = Column(String(128), nullable=True)
    seniority = Column(String(64), nullable=True)
    employment_type = Column(String(64), nullable=True)

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(16), nullable=True)

    location_city = Column(String(128), nullable=True)
    location_region = Column(String(128), nullable=True)
    location_country = Column(String(128), nullable=True)
    remote_flag = Column(Boolean, nullable=True)

    raw_skills = Column(JSONB, nullable=True)
    canonical_skills = Column(JSONB, nullable=True)
    extra_json = Column(JSONB, nullable=True)

    job_posting = relationship("JobPosting", back_populates="extraction")

    __table_args__ = (
        Index("ix_ext_remote_flag", "remote_flag"),
        Index("ix_ext_seniority", "seniority"),
        Index("ix_ext_hiring_function", "hiring_function"),
        Index("ix_ext_salary_min", "salary_min"),
        Index("ix_ext_salary_max", "salary_max"),
        Index("ix_ext_location_city", "location_city"),
        Index("ix_ext_location_region", "location_region"),
        Index("ix_ext_location_country", "location_country"),
        CheckConstraint("salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max", name="ck_salary_range"),
    )


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    canonical_name = Column(String(128), nullable=False, unique=True)
    aliases_json = Column(JSONB, nullable=True)  # optional array


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

    job_posting = relationship("JobPosting", back_populates="job_skills")
    skill = relationship("Skill")

    __table_args__ = (
        Index("ix_job_skills_skill_id", "skill_id"),
    )
