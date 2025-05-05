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

def check_selfie_data():
    """Check the current state of selfie data in the production database"""
    try:
        # Connect to the database
        with engine.connect() as conn:
            # Check if the columns exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'attendances' 
                AND column_name IN ('selfie_path', 'selfie_data', 'selfie_content_type')
            """))
            
            columns = [row[0] for row in result]
            print(f"Columns in attendances table: {columns}")
            
            # Count total records
            result = conn.execute(text("SELECT COUNT(*) FROM attendances"))
            total_count = result.scalar()
            print(f"Total attendance records: {total_count}")
            
            # Count records with selfie paths
            result = conn.execute(text("SELECT COUNT(*) FROM attendances WHERE selfie_path IS NOT NULL"))
            path_count = result.scalar()
            print(f"Records with selfie paths: {path_count}")
            
            # If selfie_data column exists, count records with data
            if 'selfie_data' in columns:
                result = conn.execute(text("SELECT COUNT(*) FROM attendances WHERE selfie_data IS NOT NULL"))
                data_count = result.scalar()
                print(f"Records with selfie data: {data_count}")
                
                # Check records with paths but no data
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM attendances 
                    WHERE selfie_path IS NOT NULL 
                    AND (selfie_data IS NULL OR selfie_data = '')
                """))
                missing_data_count = result.scalar()
                print(f"Records with paths but no data: {missing_data_count}")
                
                # Sample some records
                result = conn.execute(text("""
                    SELECT id, selfie_path, 
                           CASE WHEN selfie_data IS NOT NULL THEN 'Has data' ELSE 'No data' END as data_status,
                           selfie_content_type
                    FROM attendances
                    WHERE selfie_path IS NOT NULL
                    LIMIT 5
                """))
                
                print("\nSample records:")
                for row in result:
                    print(f"ID: {row[0]}, Path: {row[1]}, Data: {row[2]}, Content Type: {row[3]}")
            
    except Exception as e:
        print(f"Database error: {str(e)}")

if __name__ == "__main__":
    check_selfie_data()
