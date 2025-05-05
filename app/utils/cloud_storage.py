import os
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from datetime import datetime
import logging
import aiofiles
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.getenv("CLOUDINARY_API_KEY", ""),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "")
)

class CloudStorage:
    @staticmethod
    async def upload_selfie(file: UploadFile, roll_no: str, session_id: str) -> str:
        """
        Upload a selfie to Cloudinary and return the URL
        Falls back to local storage if Cloudinary is not configured
        """
        try:
            # Check if Cloudinary is configured
            if not os.getenv("CLOUDINARY_CLOUD_NAME"):
                return await CloudStorage._save_locally(file, roll_no, session_id)
                
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{roll_no}_{session_id}_{timestamp}"
            
            # Read file content
            contents = await file.read()
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                contents,
                public_id=filename,
                folder="qr_attendance_selfies",
                resource_type="image"
            )
            
            logger.info(f"Uploaded selfie to Cloudinary: {result['secure_url']}")
            return result["secure_url"]
        except Exception as e:
            logger.error(f"Error uploading to Cloudinary: {str(e)}")
            # Fall back to local storage
            return await CloudStorage._save_locally(file, roll_no, session_id)
    
    @staticmethod
    async def _save_locally(file: UploadFile, roll_no: str, session_id: str) -> str:
        """Save file to local storage as fallback"""
        try:
            # Reset file position
            await file.seek(0)
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{roll_no}_{session_id}_{timestamp}.jpg"
            
            # Ensure directory exists
            selfie_dir = Path("static/selfies")
            selfie_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = selfie_dir / filename
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
                
            logger.info(f"Saved selfie locally: {file_path}")
            return f"static/selfies/{filename}"
        except Exception as e:
            logger.error(f"Error saving file locally: {str(e)}")
            return f"static/selfies/error_{roll_no}.jpg"
