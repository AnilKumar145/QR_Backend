import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print("Updating alembic_version table in PRODUCTION...")
print("WARNING: This will modify the production database!")

# Ask for confirmation before proceeding
confirm = input("\nAre you sure you want to proceed with modifying the production database? (y/n): ")
if confirm.lower() != 'y':
    print("Operation cancelled.")
    sys.exit(0)

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = False
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
        print(f"Current versions in production: {versions}")
        
        # Update to latest version
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('add_details_column_safe')
        """)
        print("Updated alembic_version table to latest version: add_details_column_safe")
    else:
        # Create alembic_version table with latest version
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        cursor.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('add_details_column_safe')
        """)
        print("Created alembic_version table with latest version: add_details_column_safe")
    
    # Commit the transaction
    conn.commit()
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    print("\nProduction alembic_version updated successfully!")
    
except Exception as e:
    # Rollback on error
    if 'conn' in locals() and conn:
        conn.rollback()
    print(f"Error updating production alembic_version: {e}")
    sys.exit(1)