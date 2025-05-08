"""add missing selfie columns

Revision ID: add_missing_selfie_columns
Revises: da48b3799e92
Create Date: 2023-05-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import BYTEA

# revision identifiers, used by Alembic
revision = 'add_missing_selfie_columns'
down_revision = 'da48b3799e92'  # This should be the current head
branch_labels = None
depends_on = None

def upgrade():
    # Check if columns exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('attendances')]
    
    # Add selfie_data column if it doesn't exist
    if 'selfie_data' not in columns:
        op.add_column('attendances', sa.Column('selfie_data', BYTEA(), nullable=True))
    
    # Add selfie_content_type column if it doesn't exist
    if 'selfie_content_type' not in columns:
        op.add_column('attendances', sa.Column('selfie_content_type', sa.String(), nullable=True))

def downgrade():
    # Only drop columns if they exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('attendances')]
    
    if 'selfie_content_type' in columns:
        op.drop_column('attendances', 'selfie_content_type')
    
    if 'selfie_data' in columns:
        op.drop_column('attendances', 'selfie_data')