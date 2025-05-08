"""merge add_selfie_data_columns

Revision ID: da48b3799e92
Revises: add_selfie_data_columns, e236aececf36
Create Date: 2025-05-05 12:51:19.071400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da48b3799e92'
down_revision: Union[str, None] = ('add_selfie_data_columns', 'e236aececf36')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
