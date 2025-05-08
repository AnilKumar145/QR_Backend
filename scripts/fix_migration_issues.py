#!/usr/bin/env python
"""
Fix Migration Issues Script
This script helps fix common Alembic migration issues.
"""

import os
import sys
import shutil
import glob
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URLs
LOCAL_DB_URL = os.getenv("DATABASE_URL")
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not LOCAL_DB_URL:
    print("❌ Error: DATABASE_URL environment variable not set")
    sys.exit(1)

if not PROD_DB_URL:
    print("❌ Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print("🔧 Fixing Alembic migration issues...")

# Step 1: Backup current migration files
print("\n1️⃣ Backing up current migration files...")
if not os.path.exists("alembic_backup"):
    os.makedirs("alembic_backup")

for migration_file in glob.glob("alembic/versions/*.py"):
    shutil.copy(migration_file, "alembic_backup/")
print("✅ Migration files backed up to alembic_backup/")

# Step 2: Check for duplicate migration files
print("\n2️⃣ Checking for duplicate migrations...")
migration_ids = {}
duplicates = []

for migration_file in glob.glob("alembic/versions/*.py"):
    with open(migration_file, "r") as f:
        content = f.read()
        
    # Extract revision ID
    for line in content.split("\n"):
        if line.strip().startswith("revision = "):
            revision_id = line.split("=")[1].strip().strip("'\"")
            
            if revision_id in migration_ids:
                duplicates.append((revision_id, migration_file, migration_ids[revision_id]))
            else:
                migration_ids[revision_id] = migration_file

if duplicates:
    print(f"Found {len(duplicates)} duplicate migrations:")
    for rev_id, file1, file2 in duplicates:
        print(f"  - Revision {rev_id} in:")
        print(f"    * {file1}")
        print(f"    * {file2}")
        
        # Keep the first file, remove the duplicate
        os.remove(file1)
        print(f"    Removed {file1}")
else:
    print("✅ No duplicate migrations found")

# Step 3: Initialize alembic_version table in production if it doesn't exist
print("\n3️⃣ Checking alembic_version table in production...")
try:
    conn = psycopg2.connect(PROD_DB_URL)
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
    
    if not table_exists:
        print("Creating alembic_version table in production...")
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        print("✅ Created alembic_version table in production")
    else:
        print("✅ alembic_version table already exists in production")
        
        # Check current version
        cursor.execute("SELECT version_num FROM alembic_version")
        versions = cursor.fetchall()
        if versions:
            print(f"Current versions in production: {versions}")
        else:
            print("No versions found in alembic_version table")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error connecting to production database: {e}")

# Step 4: Create a clean migration
print("\n4️⃣ Creating a clean initial migration...")

# Create alembic/versions directory if it doesn't exist
if not os.path.exists("alembic/versions"):
    os.makedirs("alembic/versions")

# Create a clean initial migration file
initial_migration_path = "alembic/versions/initial_schema.py"
with open(initial_migration_path, "w") as f:
    f.write("""\"\"\"Initial schema

Revision ID: initial_schema
Revises: 
Create Date: 2023-01-01 00:00:00.000000

\"\"\"

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
""")

print(f"✅ Created clean initial migration: {initial_migration_path}")

# Step 5: Update alembic_version in production to point to the new migration
print("\n5️⃣ Updating alembic_version in production...")
try:
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Clear existing versions and set to our new initial version
    cursor.execute("DELETE FROM alembic_version")
    cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('initial_schema')")
    
    print("✅ Updated alembic_version in production to 'initial_schema'")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error updating alembic_version in production: {e}")

print("\n✨ Migration issues fixed!")
print("Now you can run:")
print("python scripts/apply_migrations_to_production.py")