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

print("Adding columns to flagged_logs table in PRODUCTION...")
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
    
    # Check if the details column exists
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'flagged_logs' AND column_name = 'details'
    """)
    details_exists = cursor.fetchone() is not None
    
    # Check if the roll_no column exists
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'flagged_logs' AND column_name = 'roll_no'
    """)
    rollno_exists = cursor.fetchone() is not None
    
    # Add details column if it doesn't exist
    if not details_exists:
        print("Adding details column to flagged_logs table in PRODUCTION...")
        cursor.execute("""
            ALTER TABLE flagged_logs 
            ADD COLUMN details TEXT
        """)
        print("details column added successfully to PRODUCTION!")
    else:
        print("details column already exists in PRODUCTION.")
    
    # Add roll_no column if it doesn't exist
    if not rollno_exists:
        print("Adding roll_no column to flagged_logs table in PRODUCTION...")
        cursor.execute("""
            ALTER TABLE flagged_logs 
            ADD COLUMN roll_no VARCHAR(50)
        """)
        print("roll_no column added successfully to PRODUCTION!")
    else:
        print("roll_no column already exists in PRODUCTION.")
    
    # Commit the transaction
    conn.commit()
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    print("\nProduction database updated successfully!")
    
except Exception as e:
    # Rollback on error
    if 'conn' in locals() and conn:
        conn.rollback()
    print(f"Error updating production database: {e}")
    sys.exit(1)