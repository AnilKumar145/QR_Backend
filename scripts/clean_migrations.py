import os
import sys
import glob
import shutil
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Get the database URL
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

print("Cleaning up problematic migration files...")

# Create a backup directory for the migration files
backup_dir = "alembic/versions_backup"
os.makedirs(backup_dir, exist_ok=True)

# Find all migration files
migration_files = glob.glob("alembic/versions/*.py")
problematic_files = []

# Look for files with 'your_previous_revision_id'
for file_path in migration_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'your_previous_revision_id' in content:
            problematic_files.append(file_path)
            print(f"Found problematic file: {file_path}")

# Ask for confirmation before moving files
if problematic_files:
    confirm = input(f"\nFound {len(problematic_files)} problematic files. Move them to backup? (y/n): ")
    if confirm.lower() == 'y':
        for file_path in problematic_files:
            filename = os.path.basename(file_path)
            backup_path = os.path.join(backup_dir, filename)
            shutil.move(file_path, backup_path)
            print(f"Moved {file_path} to {backup_path}")
    else:
        print("Operation cancelled.")
        sys.exit(0)
else:
    print("No problematic files found.")

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
        # Get current version
        cursor.execute("SELECT version_num FROM alembic_version")
        versions = cursor.fetchall()
        print(f"Current versions in alembic_version table: {versions}")
        
        # Update to a known good version
        cursor.execute("DELETE FROM alembic_version")
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

print("\nMigration files cleaned up and alembic_version table fixed.")
print("Now you can create a new migration with:")
print("alembic revision --autogenerate -m \"add created_at to attendances\"")
print("And then apply it with:")
print("python scripts/apply_local_migration.py")