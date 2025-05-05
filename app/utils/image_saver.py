import os
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from datetime import datetime

# Configure Cloudinary
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

class ImageSaver:
    @classmethod
    async def save_selfie(
        cls, 
        file: UploadFile, 
        roll_no: str, 
        session_id: str
    ) -> str:
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{roll_no}_{session_id}_{timestamp}"
        
        # Read file content
        content = await file.read()
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            content,
            public_id=filename,
            folder="qr_attendance_selfies"
        )
        
        # Return the secure URL
        return result["secure_url"]
