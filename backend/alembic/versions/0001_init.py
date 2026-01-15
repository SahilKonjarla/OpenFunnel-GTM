"""init

Revision ID: 0001
Revises: 
Create Date: 2026-01-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_table(
        "raw_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_raw_responses_url_hash", "raw_responses", ["url_hash"])

    op.create_table(
        "job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("company_name", sa.String(length=256), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("location_raw", sa.String(length=512), nullable=True),
        sa.Column("location_city", sa.String(length=128), nullable=True),
        sa.Column("location_state", sa.String(length=64), nullable=True),
        sa.Column("location_country", sa.String(length=64), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=16), nullable=True),
        sa.Column("seniority", sa.String(length=64), nullable=True),
        sa.Column("role_function", sa.String(length=128), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("technologies", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="discovered"),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_job_postings_company_name", "job_postings", ["company_name"])
    op.create_index("ix_job_postings_title", "job_postings", ["title"])
    op.create_index("ix_job_postings_external_id", "job_postings", ["external_id"])
    op.create_index("ix_job_postings_location_city", "job_postings", ["location_city"])
    op.create_index("ix_job_postings_salary_min", "job_postings", ["salary_min"])
    op.create_index("ix_job_postings_salary_max", "job_postings", ["salary_max"])
    op.create_index("ix_job_postings_status", "job_postings", ["status"])
    op.create_index("ix_job_postings_company_title", "job_postings", ["company_name", "title"])

def downgrade():
    op.drop_index("ix_job_postings_company_title", table_name="job_postings")
    op.drop_table("job_postings")
    op.drop_index("ix_raw_responses_url_hash", table_name="raw_responses")
    op.drop_table("raw_responses")
    op.drop_table("runs")
