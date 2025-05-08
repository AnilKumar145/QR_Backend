"""add institutions and venues

Revision ID: add_institutions_venues
Revises: previous_revision_id
Create Date: 2023-05-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_institutions_venues'
down_revision = 'previous_revision_id'  # replace with your actual previous revision
branch_labels = None
depends_on = None

def upgrade():
    # Create institutions table
    op.create_table(
        'institutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
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

def downgrade():
    # Remove foreign key and column from qr_sessions
    op.drop_constraint('fk_qr_sessions_venue_id', 'qr_sessions', type_='foreignkey')
    op.drop_column('qr_sessions', 'venue_id')
    
    # Drop venues table
    op.drop_table('venues')
    
    # Drop institutions table
    op.drop_table('institutions')
