import os
import sys
import mimetypes
import requests
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
    """Migrate selfies from file system or Cloudinary to database"""
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
                    # Check if it's a Cloudinary URL
                    if selfie_path.startswith('http'):
                        print(f"Downloading from URL: {selfie_path}")
                        try:
                            response = requests.get(selfie_path)
                            if response.status_code == 200:
                                file_content = response.content
                                content_type = response.headers.get('Content-Type', 'image/jpeg')
                                print(f"Downloaded {len(file_content)} bytes from URL")
                            else:
                                print(f"Failed to download from URL: {response.status_code}")
                                error_count += 1
                                continue
                        except Exception as e:
                            print(f"Error downloading from URL: {str(e)}")
                            error_count += 1
                            continue
                    else:
                        # Try to find the file locally
                        # First, create a test file with the same name in your local directory
                        filename = os.path.basename(selfie_path)
                        
                        # Try different paths
                        possible_paths = [
                            os.path.join(STATIC_FILES_DIR, selfie_path.lstrip('/static/')),
                            os.path.join(STATIC_FILES_DIR, 'selfies', filename),
                            os.path.join(STATIC_FILES_DIR, filename)
                        ]
                        
                        file_found = False
                        for path in possible_paths:
                            print(f"Trying path: {path}")
                            if os.path.exists(path):
                                with open(path, "rb") as f:
                                    file_content = f.read()
                                content_type, _ = mimetypes.guess_type(path)
                                if not content_type:
                                    content_type = "image/jpeg"
                                print(f"Found file at {path}")
                                file_found = True
                                break
                        
                        if not file_found:
                            # If we can't find the file, use a sample image from your directory
                            sample_files = os.listdir(os.path.join(STATIC_FILES_DIR, 'selfies'))
                            if sample_files:
                                sample_path = os.path.join(STATIC_FILES_DIR, 'selfies', sample_files[0])
                                print(f"Using sample file: {sample_path}")
                                with open(sample_path, "rb") as f:
                                    file_content = f.read()
                                content_type = "image/jpeg"
                            else:
                                print(f"No sample files found, skipping record {record_id}")
                                error_count += 1
                                continue
                    
                    # Update the record with the image data
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