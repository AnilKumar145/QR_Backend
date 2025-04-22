"""add created_at to attendance

Revision ID: 2024_01_25_add_created_at
Revises: 2024_01_24_update_qr
Create Date: 2024-01-25 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC


# revision identifiers, used by Alembic.
revision: str = '2024_01_25_add_created_at'
down_revision: Union[str, None] = '2024_01_24_update_qr'  # Fixed revision ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.drop_column('attendances', 'created_at')

