"""add_institutions_and_venues_manual

Revision ID: xxxxxxxxxxxx
Revises: 2b478ceed7f7
Create Date: 2023-xx-xx

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'xxxxxxxxxxxx'  # Leave this as is, it will be auto-generated
down_revision: Union[str, None] = '2b478ceed7f7'  # Use your current head revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create institutions table
    op.create_table(
        'institutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create venues table
    op.create_table(
        'venues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('radius_meters', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add venue_id to qr_sessions
    op.add_column('qr_sessions', sa.Column('venue_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_qr_sessions_venue_id', 'qr_sessions', 'venues', ['venue_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key and column from qr_sessions
    op.drop_constraint('fk_qr_sessions_venue_id', 'qr_sessions', type_='foreignkey')
    op.drop_column('qr_sessions', 'venue_id')
    
    # Drop venues table
    op.drop_table('venues')
    
    # Drop institutions table
    op.drop_table('institutions')