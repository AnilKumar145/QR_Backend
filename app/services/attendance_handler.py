from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.attendance import Attendance
from app.models.qr_session import QRSession
from app.models.flagged_log import FlaggedLog
from app.schemas.attendance import AttendanceCreate
from app.services.geo_validation import GeoValidator
from app.utils.image_saver import ImageSaver

class AttendanceHandler:
    def __init__(self, db: Session):
        self.db = db
        self.geo_validator = GeoValidator()
        self.image_saver = ImageSaver()

    def validate_session(self, session_id: str) -> Optional[QRSession]:
        session = self.db.query(QRSession).filter(
            QRSession.session_id == session_id
        ).first()
        
        if not session or session.expires_at < datetime.utcnow():
            return None
        return session

    async def process_attendance(
        self, 
        attendance_data: AttendanceCreate, 
        selfie: UploadFile
    ) -> Tuple[bool, str]:
        # Validate session
        session = self.validate_session(attendance_data.session_id)
        if not session:
            return False, "Invalid or expired session"

        # Validate location
        is_valid_location, distance = self.geo_validator.is_location_valid(
            attendance_data.location_lat,
            attendance_data.location_lon
        )

        # Save selfie
        selfie_path = await self.image_saver.save_selfie(
            selfie, 
            attendance_data.roll_no,
            attendance_data.session_id
        )

        # Create attendance record
        attendance = Attendance(
            **attendance_data.dict(),
            selfie_path=selfie_path,
            is_valid_location=is_valid_location
        )
        self.db.add(attendance)

        # Log if location is invalid
        if not is_valid_location:
            flagged_log = FlaggedLog(
                session_id=attendance_data.session_id,
                reason="Invalid Location",
                details=f"Distance from institution: {distance:.2f} km"
            )
            self.db.add(flagged_log)

        self.db.commit()
        return True, "Attendance recorded successfully"