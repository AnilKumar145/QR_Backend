"""fix_created_at_attendances

Revision ID: fix_created_at_attendances
Revises: 2b478ceed7f7
Create Date: 2023-07-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'fix_created_at_attendances'
down_revision: Union[str, None] = '2b478ceed7f7'  # Using the last valid revision from your history
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column exists before adding it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('attendances')]
    
    if 'created_at' not in columns:
        # Add created_at column with timezone support
        op.add_column('attendances',
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True)
        )
        
        # Update existing rows to use timestamp value for created_at
        op.execute("""
            UPDATE attendances 
            SET created_at = timestamp AT TIME ZONE 'UTC'
            WHERE created_at IS NULL
        """)
        
        # Make created_at non-nullable after data migration
        op.alter_column('attendances', 'created_at',
                        existing_type=sa.DateTime(timezone=True),
                        nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Check if column exists before dropping it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('attendances')]
    
    if 'created_at' in columns:
        op.drop_column('attendances', 'created_at')