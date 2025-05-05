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