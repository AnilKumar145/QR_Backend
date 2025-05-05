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

print(f"Connecting to: {PROD_DB_URL}")

try:
    # Connect directly with psycopg2
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
    
    if not table_exists:
        print("Creating alembic_version table...")
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        
        # Insert the latest version
        cursor.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('add_missing_selfie_columns')
        """)
        
        conn.commit()
        print("Alembic version table created and initialized!")
    else:
        print("Alembic version table already exists")
        
        # Check current version
        cursor.execute("SELECT version_num FROM alembic_version")
        versions = cursor.fetchall()
        print(f"Current versions: {versions}")
        
        # Update to latest version if needed
        if not any(row[0] == 'add_missing_selfie_columns' for row in versions):
            cursor.execute("DELETE FROM alembic_version")
            cursor.execute("""
                INSERT INTO alembic_version (version_num) 
                VALUES ('add_missing_selfie_columns')
            """)
            conn.commit()
            print("Updated to latest version: add_missing_selfie_columns")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")