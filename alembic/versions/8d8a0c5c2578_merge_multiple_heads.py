"""merge multiple heads

Revision ID: 8d8a0c5c2578
Revises: 20240506_add_is_active, add_created_at_to_attendances, fix_created_at_attendances
Create Date: 2025-05-06 10:11:22.880235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d8a0c5c2578'
down_revision: Union[str, None] = ('20240506_add_is_active', 'add_created_at_to_attendances', 'fix_created_at_attendances')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
