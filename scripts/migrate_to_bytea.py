import os
import sys
import asyncio
import requests
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your models and database connection
from app.db.base import SessionLocal
from app.models.attendance import Attendance

async def migrate_images_to_bytea():
    """Migrate images from paths/URLs to BYTEA in database"""
    db = SessionLocal()
    try:
        # Get all attendance records with selfie paths but no binary data
        records = db.query(Attendance).filter(
            Attendance.selfie_path.isnot(None),
            Attendance.selfie_data.is_(None)
        ).all()
        
        print(f"Found {len(records)} records with selfie paths but no binary data")
        
        for record in records:
            try:
                path = record.selfie_path
                
                # Handle local files
                if path.startswith("static/"):
                    full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
                    if os.path.exists(full_path):
                        with open(full_path, "rb") as f:
                            image_data = f.read()
                        content_type = "image/jpeg"  # Assume JPEG for local files
                    else:
                        print(f"File not found: {full_path}")
                        continue
                
                # Handle remote URLs (Cloudinary)
                elif path.startswith("http"):
                    response = requests.get(path)
                    if response.status_code == 200:
                        image_data = response.content
                        content_type = response.headers.get("Content-Type", "image/jpeg")
                    else:
                        print(f"Failed to download {path}: {response.status_code}")
                        continue
                else:
                    print(f"Unrecognized path format: {path}")
                    continue
                
                # Update the record
                record.selfie_data = image_data
                record.selfie_content_type = content_type
                db.commit()
                print(f"Updated record {record.id} with binary data")
                
            except Exception as e:
                print(f"Error processing record {record.id}: {str(e)}")
                db.rollback()
        
        print("Migration completed")
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(migrate_to_bytea())