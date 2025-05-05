"""fix_created_at_in_qr_sessions

Revision ID: 67e0d31d3fef
Revises: 65e0d31d3fef
Create Date: 2025-05-06 12:15:27.206247

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = '67e0d31d3fef'
down_revision: Union[str, None] = '65e0d31d3fef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update any NULL created_at values to current timestamp
    op.execute(text("UPDATE qr_sessions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    
    # Make created_at non-nullable with a default value
    op.alter_column('qr_sessions', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.func.now())


def downgrade() -> None:
    """Downgrade schema."""
    # Make created_at nullable again and remove server default
    op.alter_column('qr_sessions', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True,
                    server_default=None)