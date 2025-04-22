from datetime import datetime, timedelta, UTC
import uuid
import json
import qrcode
from io import BytesIO
import base64
from typing import Tuple
from app.core.config import settings

class QRGenerator:
    @staticmethod
    def generate_session_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def create_qr_data(session_id: str, expires_at: datetime) -> str:
        # Create a direct URL using HTTPS
        return f"https://qr-frontend-gmx7-anilkumar145s-projects.vercel.app/mark-attendance/{session_id}"

    @staticmethod
    def generate_qr_code(data: str) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # Add the URL directly, no JSON encoding needed
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"

    @classmethod
    def create_session_qr(cls, duration_minutes: int = 2) -> Tuple[str, datetime, str]:
        session_id = cls.generate_session_id()
        expires_at = datetime.now(UTC) + timedelta(minutes=duration_minutes)
        qr_data = cls.create_qr_data(session_id, expires_at)
        qr_image = cls.generate_qr_code(qr_data)
        
        return session_id, expires_at, qr_image








