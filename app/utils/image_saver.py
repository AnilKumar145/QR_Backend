import os
from fastapi import UploadFile
from datetime import datetime

class ImageSaver:
    SELFIE_DIR = "static/selfies"

    @classmethod
    async def save_selfie(
        cls, 
        file: UploadFile, 
        roll_no: str, 
        session_id: str
    ) -> str:
        # Create directory if it doesn't exist
        os.makedirs(cls.SELFIE_DIR, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{roll_no}_{session_id}_{timestamp}.jpg"
        file_path = os.path.join(cls.SELFIE_DIR, filename)

        # Save the file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        return file_path