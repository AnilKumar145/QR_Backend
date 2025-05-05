import os
import sys
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print("Adding created_at column to attendances table in PRODUCTION...")
print("WARNING: This will modify the production database!")

# Ask for confirmation before proceeding
confirm = input("\nAre you sure you want to proceed with modifying the production database? (y/n): ")
if confirm.lower() != 'y':
    print("Operation cancelled.")
    sys.exit(0)

# Connect to the database
try:
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = False  # Use transaction
    cursor = conn.cursor()
    
    # Check if created_at column exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'attendances' AND column_name = 'created_at'
        )
    """)
    column_exists = cursor.fetchone()[0]
    
    if not column_exists:
        print("Adding created_at column to PRODUCTION...")
        
        # Add created_at column
        cursor.execute("""
            ALTER TABLE attendances 
            ADD COLUMN created_at TIMESTAMP WITH TIME ZONE
        """)
        
        # Update existing rows to use timestamp value for created_at
        cursor.execute("""
            UPDATE attendances 
            SET created_at = timestamp AT TIME ZONE 'UTC'
            WHERE created_at IS NULL
        """)
        
        # Make created_at non-nullable
        cursor.execute("""
            ALTER TABLE attendances 
            ALTER COLUMN created_at SET NOT NULL
        """)
        
        # Commit the transaction
        conn.commit()
        print("created_at column added successfully to PRODUCTION!")
    else:
        print("created_at column already exists in PRODUCTION.")
        conn.rollback()
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    # Rollback on error
    if conn:
        conn.rollback()
    print(f"Error adding created_at column to PRODUCTION: {e}")
    sys.exit(1)

print("\nDone!")