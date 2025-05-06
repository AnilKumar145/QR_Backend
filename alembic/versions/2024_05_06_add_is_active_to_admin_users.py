"""Add is_active column to admin_users table

Revision ID: 20240506_add_is_active
Revises: 20240428_add_admin_user_table
Create Date: 2024-05-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240506_add_is_active'
down_revision = '20240428_add_admin_user_table'
branch_labels = None
depends_on = None

def upgrade():
    # Add is_active column with default value True
    op.add_column('admin_users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

def downgrade():
    op.drop_column('admin_users', 'is_active')