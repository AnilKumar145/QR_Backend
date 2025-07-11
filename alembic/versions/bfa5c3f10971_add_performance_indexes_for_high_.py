"""Add performance indexes for high concurrency

Revision ID: bfa5c3f10971
Revises: 5f5f47055c62
Create Date: 2025-07-12 09:37:42.600143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfa5c3f10971'
down_revision: Union[str, None] = '5f5f47055c62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('idx_attendance_branch_section', 'attendances', ['branch', 'section'], unique=False)
    op.create_index('idx_attendance_session_roll', 'attendances', ['session_id', 'roll_no'], unique=False)
    op.create_index('idx_attendance_venue_time', 'attendances', ['venue_id', 'timestamp'], unique=False)
    op.create_index(op.f('ix_attendances_created_at'), 'attendances', ['created_at'], unique=False)
    op.create_index(op.f('ix_attendances_roll_no'), 'attendances', ['roll_no'], unique=False)
    op.create_index(op.f('ix_attendances_session_id'), 'attendances', ['session_id'], unique=False)
    op.create_index(op.f('ix_attendances_venue_id'), 'attendances', ['venue_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_attendances_venue_id'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_session_id'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_roll_no'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_created_at'), table_name='attendances')
    op.drop_index('idx_attendance_venue_time', table_name='attendances')
    op.drop_index('idx_attendance_session_roll', table_name='attendances')
    op.drop_index('idx_attendance_branch_section', table_name='attendances')
    # ### end Alembic commands ###
