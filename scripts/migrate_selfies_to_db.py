import os
import sys
import mimetypes
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

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

# Define the static files directory
STATIC_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

def migrate_selfies_to_db():
    """Migrate selfies from file system to database using raw SQL"""
    try:
        # Connect to the database
        with engine.connect() as conn:
            # Get all attendance records with selfie paths but no binary data
            result = conn.execute(text("""
                SELECT id, selfie_path 
                FROM attendances 
                WHERE selfie_path IS NOT NULL 
                AND (selfie_data IS NULL OR selfie_data = '')
            """))
            
            records = result.fetchall()
            print(f"Found {len(records)} records with selfie paths but no binary data")
            
            migrated_count = 0
            error_count = 0
            
            for record in records:
                record_id = record[0]
                selfie_path = record[1]
                
                try:
                    # Get the file path - fix the 'elfies' to 'selfies' if needed
                    relative_path = selfie_path.lstrip('/static/')
                    if 'elfies' in relative_path:
                        relative_path = relative_path.replace('elfies', 'selfies')
                    
                    file_path = os.path.join(STATIC_FILES_DIR, relative_path)
                    print(f"Looking for file: {file_path}")
                    
                    # Try alternative paths if the file doesn't exist
                    if not os.path.exists(file_path):
                        # Try with 'selfies' folder
                        alt_path = os.path.join(STATIC_FILES_DIR, 'selfies', os.path.basename(file_path))
                        print(f"Trying alternative path: {alt_path}")
                        if os.path.exists(alt_path):
                            file_path = alt_path
                    
                    if os.path.exists(file_path):
                        # Read the file content
                        with open(file_path, "rb") as f:
                            file_content = f.read()
                        
                        # Determine content type
                        content_type, _ = mimetypes.guess_type(file_path)
                        if not content_type:
                            content_type = "image/jpeg"  # Default to JPEG
                        
                        # Update the record using raw SQL
                        conn.execute(
                            text("""
                                UPDATE attendances 
                                SET selfie_data = :data, 
                                    selfie_content_type = :content_type 
                                WHERE id = :id
                            """),
                            {
                                "data": file_content,
                                "content_type": content_type,
                                "id": record_id
                            }
                        )
                        conn.commit()
                        
                        print(f"Migrated selfie for record {record_id} ({len(file_content)} bytes)")
                        migrated_count += 1
                    else:
                        # Check if the selfies directory exists
                        selfies_dir = os.path.join(STATIC_FILES_DIR, 'selfies')
                        if os.path.exists(selfies_dir):
                            print(f"Selfies directory exists: {selfies_dir}")
                            print(f"Files in selfies directory: {os.listdir(selfies_dir)}")
                        else:
                            print(f"Selfies directory does not exist: {selfies_dir}")
                        
                        print(f"File not found for record {record_id}: {file_path}")
                        error_count += 1
                except Exception as e:
                    print(f"Error migrating selfie for record {record_id}: {str(e)}")
                    error_count += 1
            
            print(f"\nMigration complete:")
            print(f"- Total records processed: {len(records)}")
            print(f"- Successfully migrated: {migrated_count}")
            print(f"- Errors: {error_count}")
    
    except Exception as e:
        print(f"Database error: {str(e)}")

if __name__ == "__main__":
    migrate_selfies_to_db()




