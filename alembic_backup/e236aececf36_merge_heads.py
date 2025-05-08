"""merge heads

Revision ID: e236aececf36
Revises: 20240428_add_admin_user_table, bba8cbf9d3c8
Create Date: 2025-04-29 10:32:54.620270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e236aececf36'
down_revision: Union[str, None] = ('20240428_add_admin_user_table', 'bba8cbf9d3c8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
