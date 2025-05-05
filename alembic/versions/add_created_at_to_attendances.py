"""add created_at to attendances table

Revision ID: add_created_at_to_attendances
Revises: da48b3799e92
Create Date: 2023-07-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'add_created_at_to_attendances'
down_revision: Union[str, None] = 'da48b3799e92'  # Update this to your latest revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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
    op.drop_column('attendances', 'created_at')