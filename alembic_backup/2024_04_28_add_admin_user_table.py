"""Add admin_users table

Revision ID: 20240428_add_admin_user_table
Revises: 
Create Date: 2024-04-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240428_add_admin_user_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('username', sa.String(length=50), unique=True, index=True, nullable=False),
        sa.Column('hashed_password', sa.String(length=128), nullable=False),
        sa.Column('is_admin', sa.Boolean, nullable=False, default=True),
    )

def downgrade():
    op.drop_table('admin_users')
