"""add created_at to attendance

Revision ID: add_created_at_to_attendance
Revises: your_previous_revision_id
Create Date: 2023-07-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'add_created_at_to_attendance'
down_revision = 'your_previous_revision_id'  # Replace with your actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Add created_at column with default value of current timestamp
    op.add_column('attendances', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()))


def downgrade():
    # Remove created_at column
    op.drop_column('attendances', 'created_at')