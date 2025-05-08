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
    """Create initial schema based on production database."""
    # Create qr_sessions table
    op.create_table('qr_sessions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('qr_image', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create flagged_logs table
    op.create_table('flagged_logs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('details', sa.String(), nullable=True),
        sa.Column('timestamp', sa.String(), nullable=True),
        sa.Column('roll_no', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create attendances table
    op.create_table('attendances',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('roll_no', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('branch', sa.String(), nullable=True),
        sa.Column('section', sa.String(), nullable=True),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lon', sa.Float(), nullable=True),
        sa.Column('selfie_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_valid_location', sa.Boolean(), nullable=True),
        sa.Column('selfie_data', sa.LargeBinary(), nullable=True),
        sa.Column('selfie_content_type', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create admin_users table
    op.create_table('admin_users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(128), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Add foreign key from attendances.session_id to qr_sessions.session_id
    op.create_foreign_key('fk_attendances_session_id_to_qr_sessions', 'attendances', 'qr_sessions', ['session_id'], ['session_id'])

    # Create institutions table (missing in production)
    op.create_table('institutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create venues table (missing in production)
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

    # Add venue_id to qr_sessions
    op.add_column('qr_sessions', sa.Column('venue_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_qr_sessions_venue_id', 'qr_sessions', 'venues', ['venue_id'], ['id'])

def downgrade() -> None:
    """Downgrade schema."""
    # Drop venue_id from qr_sessions
    op.drop_constraint('fk_qr_sessions_venue_id', 'qr_sessions', type_='foreignkey')
    op.drop_column('qr_sessions', 'venue_id')
    # Drop venues table
    op.drop_table('venues')
    
    # Drop institutions table
    op.drop_table('institutions')
    op.drop_constraint('fk_attendances_session_id_to_qr_sessions', 'attendances', type_='foreignkey')
    op.drop_table('admin_users')
    op.drop_table('attendances')
    op.drop_table('flagged_logs')
    op.drop_table('qr_sessions')
