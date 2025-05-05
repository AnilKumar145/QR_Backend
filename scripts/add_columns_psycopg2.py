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
    
    # Check if columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'attendances' 
        AND column_name IN ('selfie_data', 'selfie_content_type')
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    print(f"Existing columns: {existing_columns}")
    
    try:
        # Add selfie_data column if it doesn't exist
        if 'selfie_data' not in existing_columns:
            print("Adding selfie_data column...")
            cursor.execute("""
                ALTER TABLE attendances 
                ADD COLUMN selfie_data BYTEA
            """)
        
        # Add selfie_content_type column if it doesn't exist
        if 'selfie_content_type' not in existing_columns:
            print("Adding selfie_content_type column...")
            cursor.execute("""
                ALTER TABLE attendances 
                ADD COLUMN selfie_content_type VARCHAR
            """)
        
        # Commit changes
        conn.commit()
        print("Columns added successfully!")
        
    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"Error adding columns: {e}")
        raise
    
    # Verify columns were added
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'attendances' 
        AND column_name IN ('selfie_data', 'selfie_content_type')
    """)
    
    updated_columns = [row[0] for row in cursor.fetchall()]
    print(f"Updated columns: {updated_columns}")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")