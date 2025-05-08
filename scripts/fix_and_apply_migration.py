import os
import sys
import subprocess
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Get the database URL
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

print("Fixing migration history and applying new migration...")

# Connect to the database to fix the alembic_version table
try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if alembic_version table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'alembic_version'
        )
    """)
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        # Drop and recreate the table
        cursor.execute("DROP TABLE alembic_version")
        print("Dropped existing alembic_version table")
        
        # Update to a known good version
        cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        cursor.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('2b478ceed7f7')
        """)
        print("Updated alembic_version table to a known good version: 2b478ceed7f7")
    else:
        # Create alembic_version table with known good version
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        cursor.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('2b478ceed7f7')
        """)
        print("Created alembic_version table with known good version: 2b478ceed7f7")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error fixing alembic_version table: {e}")
    sys.exit(1)

# Create a temporary alembic.ini with the database URL
with open("alembic.ini", "r") as f:
    alembic_config = f.read()

# Replace the sqlalchemy.url line
alembic_config = alembic_config.replace(
    "sqlalchemy.url = ", 
    f"sqlalchemy.url = {DB_URL}"
)

# Write to a temporary file
with open("alembic_fixed.ini", "w") as f:
    f.write(alembic_config)

# Create a manual migration file for institutions and venues
migration_content = """\"\"\"add_institutions_and_venues_manual

Revision ID: add_institutions_venues
Revises: 2b478ceed7f7
Create Date: 2023-05-15 12:00:00.000000

\"\"\"
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_institutions_venues'
down_revision: Union[str, None] = '2b478ceed7f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    \"\"\"Upgrade schema.\"\"\"
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
    \"\"\"Downgrade schema.\"\"\"
    # Remove foreign key and column from qr_sessions
    op.drop_constraint('fk_qr_sessions_venue_id', 'qr_sessions', type_='foreignkey')
    op.drop_column('qr_sessions', 'venue_id')
    
    # Drop venues table
    op.drop_table('venues')
    
    # Drop institutions table
    op.drop_table('institutions')
"""

# Create the migration file directly
os.makedirs("alembic/versions", exist_ok=True)
migration_path = "alembic/versions/add_institutions_venues_manual.py"
with open(migration_path, "w") as f:
    f.write(migration_content)

print(f"Created migration file: {migration_path}")

try:
    # Run alembic commands with the temporary config
    print("\nChecking current revision...")
    subprocess.run(["alembic", "-c", "alembic_fixed.ini", "current"], check=True)
    
    print("\nShowing migration history...")
    subprocess.run(["alembic", "-c", "alembic_fixed.ini", "history"], check=True)
    
    # Ask for confirmation before upgrading
    confirm = input("\nDo you want to apply the fixed migration? (y/n): ")
    if confirm.lower() == 'y':
        print("\nApplying migration...")
        subprocess.run(["alembic", "-c", "alembic_fixed.ini", "upgrade", "head"], check=True)
        print("\nMigration applied successfully!")
    else:
        print("\nMigration cancelled.")
finally:
    # Clean up the temporary file
    if os.path.exists("alembic_fixed.ini"):
        os.remove("alembic_fixed.ini")
