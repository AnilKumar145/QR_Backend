"""add selfie data columns

Revision ID: add_selfie_data_columns
Revises: bba8cbf9d3c8
Create Date: 2023-xx-xx

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_selfie_data_columns'
down_revision = 'bba8cbf9d3c8'  # Changed from 'previous_revision_id' to a valid revision
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns without removing existing ones
    op.add_column('attendances', sa.Column('selfie_data', sa.LargeBinary(), nullable=True))
    op.add_column('attendances', sa.Column('selfie_content_type', sa.String(), nullable=True))

def downgrade():
    op.drop_column('attendances', 'selfie_content_type')
    op.drop_column('attendances', 'selfie_data')
