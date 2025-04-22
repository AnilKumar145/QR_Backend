"""update qr session table

Revision ID: 2024_01_24_update_qr
Revises: 32e7a4aaa922
Create Date: 2024-01-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '2024_01_24_update_qr'
down_revision = '32e7a4aaa922'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # First update any existing NULL values to empty string
    op.execute(text("UPDATE qr_sessions SET qr_image = '' WHERE qr_image IS NULL"))
    
    # Then make the column non-nullable
    op.alter_column('qr_sessions', 'qr_image',
                    existing_type=sa.Text(),
                    nullable=False,
                    server_default='')  # Provide a default for existing rows
    
    # Finally remove the server default
    op.alter_column('qr_sessions', 'qr_image',
                    existing_type=sa.Text(),
                    server_default=None)  # Remove the default after migration

def downgrade() -> None:
    op.alter_column('qr_sessions', 'qr_image',
                    existing_type=sa.Text(),
                    nullable=True)
