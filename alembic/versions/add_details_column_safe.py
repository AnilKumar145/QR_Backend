"""add details column to flagged_logs safely

Revision ID: add_details_column_safe
Revises: merge_migration_heads
Create Date: 2023-07-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = 'add_details_column_safe'
down_revision: Union[str, None] = 'merge_migration_heads'  # Update this to your merge migration ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get database connection
    conn = op.get_bind()
    
    # Check if details column exists in flagged_logs table
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('flagged_logs')]
    
    if 'details' not in columns:
        # Add details column to flagged_logs table
        op.add_column('flagged_logs', sa.Column('details', sa.Text(), nullable=True))
        print("Added details column to flagged_logs table")
    else:
        print("details column already exists in flagged_logs table")


def downgrade() -> None:
    """Downgrade schema."""
    # Get database connection
    conn = op.get_bind()
    
    # Check if details column exists in flagged_logs table
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('flagged_logs')]
    
    if 'details' in columns:
        # Drop details column from flagged_logs table
        op.drop_column('flagged_logs', 'details')
        print("Dropped details column from flagged_logs table")
    else:
        print("details column does not exist in flagged_logs table")