"""manual fix migrations and add is_active to admin_users

Revision ID: manual_fix_migrations
Revises: 8d8a0c5c2578
Create Date: 2025-05-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect

# revision identifiers, used by Alembic.
revision: str = 'manual_fix_migrations'
down_revision: Union[str, None] = '8d8a0c5c2578'  # Your merge migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get database connection
    conn = op.get_bind()
    
    # Check if admin_users table exists
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'admin_users' in tables:
        # Check if is_active column exists in admin_users table
        columns = [col['name'] for col in inspector.get_columns('admin_users')]
        
        if 'is_active' not in columns:
            # Add is_active column to admin_users table
            op.execute(text("""
            ALTER TABLE admin_users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
            """))
            print("Added is_active column to admin_users table")
        else:
            print("is_active column already exists in admin_users table")
    else:
        print("admin_users table does not exist")


def downgrade() -> None:
    """Downgrade schema."""
    # Get database connection
    conn = op.get_bind()
    
    # Check if admin_users table exists
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'admin_users' in tables:
        # Check if is_active column exists in admin_users table
        columns = [col['name'] for col in inspector.get_columns('admin_users')]
        
        if 'is_active' in columns:
            # Drop is_active column from admin_users table
            op.execute(text("""
            ALTER TABLE admin_users DROP COLUMN is_active;
            """))
            print("Dropped is_active column from admin_users table")
        else:
            print("is_active column does not exist in admin_users table")
    else:
        print("admin_users table does not exist")