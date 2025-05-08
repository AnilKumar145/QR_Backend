"""Initial schema

Revision ID: initial_schema
Revises: 
Create Date: 2023-01-01 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # Create all tables that should exist in your current schema
    # This is a placeholder - you'll need to update this with your actual schema
    
    # Create qr_sessions table
    op.create_table('qr_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('course_code', sa.String(), nullable=False),
        sa.Column('course_name', sa.String(), nullable=False),
        sa.Column('faculty_name', sa.String(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create attendances table
    op.create_table('attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('student_name', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('selfie_path', sa.String(), nullable=True),
        sa.Column('selfie_data', sa.LargeBinary(), nullable=True),
        sa.Column('selfie_content_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create institutions table
    op.create_table('institutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create venues table
    op.create_table('venues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('geofence_radius', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key from qr_sessions to venues
    op.create_foreign_key('fk_qr_sessions_venue_id', 'qr_sessions', 'venues', ['venue_id'], ['id'])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_constraint('fk_qr_sessions_venue_id', 'qr_sessions', type_='foreignkey')
    op.drop_table('venues')
    op.drop_table('institutions')
    op.drop_table('attendances')
    op.drop_table('qr_sessions')
