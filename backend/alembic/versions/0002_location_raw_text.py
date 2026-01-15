"""location_raw to text

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-15
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column("job_postings", "location_raw", type_=sa.Text(), existing_type=sa.String(length=512))

def downgrade():
    op.alter_column("job_postings", "location_raw", type_=sa.String(length=512), existing_type=sa.Text())
