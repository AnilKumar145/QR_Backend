import os
import sys
import subprocess
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Load environment variables
load_dotenv()

# Get database URL from environment
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

# Parse database URL
# Format: postgresql://username:password@host:port/dbname
try:
    # Remove postgresql:// prefix
    db_info = db_url.split("://")[1]
    
    # Split credentials and host info
    credentials, host_info = db_info.split("@")
    
    # Get username and password
    if ":" in credentials:
        username, password = credentials.split(":")
    else:
        username = credentials
        password = ""
    
    # Get host, port, and dbname
    if "/" in host_info:
        host_port, dbname = host_info.split("/")
    else:
        host_port = host_info
        dbname = ""
    
    # Get host and port
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = "5432"  # Default PostgreSQL port
    
except Exception as e:
    print(f"Error parsing DATABASE_URL: {e}")
    sys.exit(1)

print("Connecting to database...")
try:
    # Connect to the database
    conn = psycopg2.connect(
        dbname=dbname,
        user=username,
        password=password,
        host=host,
        port=port
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if alembic_version table exists
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')")
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print("Alembic version table exists. Checking current version...")
        cursor.execute("SELECT version_num FROM alembic_version")
        versions = cursor.fetchall()
        
        if versions:
            print(f"Current versions in alembic_version table: {versions}")
            
            # Check if the problematic version exists
            has_problem_version = False
            for version in versions:
                if version[0] == 'merge_migration_heads':
                    has_problem_version = True
                    break
            
            if has_problem_version:
                print("Found problematic 'merge_migration_heads' version. Removing it...")
                cursor.execute("DELETE FROM alembic_version WHERE version_num = 'merge_migration_heads'")
                print("Removed problematic version.")
            
            # List all migration files
            print("\nListing available migration files:")
            migration_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic", "versions")
            migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.py') and not f.startswith('__')]
            
            for file in migration_files:
                print(f"  - {file}")
            
            # Find the latest valid migration
            print("\nLooking for a valid migration to use...")
            valid_migrations = []
            for file in migration_files:
                # Skip the problematic file if it exists
                if "merge_migration_heads" in file:
                    continue
                
                # Extract revision ID from filename (usually the part before the first underscore)
                revision_id = file.split('_')[0]
                if len(revision_id) >= 8:  # Most revision IDs are at least 8 chars
                    valid_migrations.append(revision_id)
            
            if valid_migrations:
                # Use the last one as current
                latest_migration = valid_migrations[-1]
                print(f"Setting current version to: {latest_migration}")
                
                # Clear the table and set to the latest valid migration
                cursor.execute("DELETE FROM alembic_version")
                cursor.execute("INSERT INTO alembic_version (version_num) VALUES (%s)", (latest_migration,))
                print("Alembic version updated successfully!")
            else:
                print("No valid migrations found. Creating a fresh alembic_version table...")
                cursor.execute("DELETE FROM alembic_version")
                print("Alembic version table emptied. You'll need to stamp a base revision.")
        else:
            print("Alembic version table is empty. No action needed.")
    else:
        print("Alembic version table doesn't exist. Creating it...")
        cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        print("Alembic version table created. You'll need to stamp a base revision.")
    
    # Close connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error fixing alembic_version table: {e}")
    sys.exit(1)

print("\nAlembic state fixed. Now you can create a new migration with:")
print("alembic revision -m \"add_institutions_and_venues_manual\"")
print("And then apply it with:")
print("python scripts/apply_local_migration.py")