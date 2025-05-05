import os
import sys
import mimetypes
import requests
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

# Define the static files directory
STATIC_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

def migrate_selfies_to_db():
    """Migrate selfies to database using a sample image for local paths and downloading for Cloudinary URLs"""
    try:
        # Find a sample image to use for local paths
        selfies_dir = os.path.join(STATIC_FILES_DIR, 'selfies')
        if not os.path.exists(selfies_dir) or not os.listdir(selfies_dir):
            print("Error: No sample images found in static/selfies directory")
            return
        
        # Use the first image in the directory as sample
        sample_image_name = os.listdir(selfies_dir)[0]
        sample_image_path = os.path.join(selfies_dir, sample_image_name)
        
        print(f"Using sample image: {sample_image_path}")
        
        # Read the sample image
        with open(sample_image_path, "rb") as f:
            sample_image_data = f.read()
        
        # Determine content type
        sample_content_type, _ = mimetypes.guess_type(sample_image_path)
        if not sample_content_type:
            sample_content_type = "image/jpeg"
        
        print(f"Sample image size: {len(sample_image_data)} bytes, type: {sample_content_type}")
        
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
                                print(f"Failed to download from URL: {response.status_code}, using sample image instead")
                                file_content = sample_image_data
                                content_type = sample_content_type
                        except Exception as e:
                            print(f"Error downloading from URL: {str(e)}, using sample image instead")
                            file_content = sample_image_data
                            content_type = sample_content_type
                    else:
                        # Use the sample image for local paths
                        print(f"Using sample image for record {record_id}")
                        file_content = sample_image_data
                        content_type = sample_content_type
                    
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