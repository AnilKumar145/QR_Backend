"""add details column to flagged_logs

Revision ID: add_details_column
Revises: a24317005e43
Create Date: 2023-07-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_details_column'
down_revision = 'a24317005e43'  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('flagged_logs', sa.Column('details', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('flagged_logs', 'details')