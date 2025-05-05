import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to production database: {PROD_DB_URL}")

# Create engine with production database
engine = create_engine(PROD_DB_URL)

def add_selfie_columns():
    """Add selfie_data and selfie_content_type columns to the attendances table"""
    try:
        # Connect to the database
        with engine.connect() as conn:
            # Check if columns exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'attendances' 
                AND column_name IN ('selfie_data', 'selfie_content_type')
            """))
            
            existing_columns = [row[0] for row in result]
            print(f"Existing columns: {existing_columns}")
            
            # Add selfie_data column if it doesn't exist
            if 'selfie_data' not in existing_columns:
                print("Adding selfie_data column...")
                conn.execute(text("""
                    ALTER TABLE attendances 
                    ADD COLUMN selfie_data BYTEA
                """))
                print("selfie_data column added successfully")
            else:
                print("selfie_data column already exists")
            
            # Add selfie_content_type column if it doesn't exist
            if 'selfie_content_type' not in existing_columns:
                print("Adding selfie_content_type column...")
                conn.execute(text("""
                    ALTER TABLE attendances 
                    ADD COLUMN selfie_content_type VARCHAR(255)
                """))
                print("selfie_content_type column added successfully")
            else:
                print("selfie_content_type column already exists")
            
            conn.commit()
            print("Column addition complete")
    
    except Exception as e:
        print(f"Database error: {str(e)}")

if __name__ == "__main__":
    add_selfie_columns()