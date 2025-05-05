from datetime import datetime, timezone, UTC
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging

from app.models.attendance import Attendance
from app.models.qr_session import QRSession
from app.models.flagged_log import FlaggedLog
from app.schemas.attendance import AttendanceCreate
from app.services.geo_validation import GeoValidator
from app.utils.image_saver import ImageSaver
from app.utils.cloud_storage import CloudStorage
from app.core.exceptions import InvalidLocationException

# Initialize logger
logger = logging.getLogger(__name__)

class AttendanceHandler:
    def __init__(self, db: Session):
        self.db = db
        self.geo_validator = GeoValidator()
        self.image_saver = ImageSaver()

    def validate_session(self, session_id: str) -> Optional[QRSession]:
        session = self.db.query(QRSession).filter(
            QRSession.session_id == session_id
        ).first()
        
        if not session or session.expires_at < datetime.now(UTC):
            return None
        return session

    async def process_attendance(
        self, 
        attendance_data: AttendanceCreate, 
        selfie: UploadFile
    ) -> Tuple[bool, str]:
        try:
            # Add debug logging
            logger.info(f"Received coordinates - Lat: {attendance_data.location_lat}, Lon: {attendance_data.location_lon}")
            logger.info(f"Campus coordinates - Lat: {self.geo_validator.INSTITUTION_LAT}, Lon: {self.geo_validator.INSTITUTION_LON}")

            # Validate session
            session = self.validate_session(attendance_data.session_id)
            if not session:
                logger.error(f"Invalid or expired session: {attendance_data.session_id}")
                return False, "Invalid or expired session"

            # Validate location and reject if invalid
            try:
                is_valid_location, distance = self.geo_validator.is_location_valid(
                    attendance_data.location_lat,
                    attendance_data.location_lon
                )
                logger.info(f"Calculated distance: {distance} km")
            except InvalidLocationException as e:
                logger.error(f"Invalid location: {str(e)}")
                return False, str(e)

            logger.info(f"Location validation result: valid={is_valid_location}, distance={distance:.2f}km")

            # Save selfie to Cloudinary or local storage
            selfie_path = await CloudStorage.upload_selfie(
                selfie,
                attendance_data.roll_no,
                attendance_data.session_id
            )
            
            logger.info(f"Selfie saved at: {selfie_path}")
            
            # Also store the selfie data in the database
            await selfie.seek(0)  # Reset file position
            selfie_content = await selfie.read()

            # Create attendance record
            attendance_dict = attendance_data.dict()
            attendance = Attendance(
                **attendance_dict,
                selfie_path=selfie_path,  # Keep storing the path
                selfie_data=selfie_content,  # Also store the binary data
                selfie_content_type=selfie.content_type,
                is_valid_location=is_valid_location,
                timestamp=datetime.now(UTC)
            )
            
            self.db.add(attendance)
            logger.info("Added attendance record to session")

            # Log if location is invalid
            if not is_valid_location:
                flagged_log = FlaggedLog(
                    session_id=attendance_data.session_id,
                    reason="Invalid Location",
                    details=f"Distance from institution: {distance:.2f} km"
                )
                self.db.add(flagged_log)
                logger.warning(f"Invalid location flagged for roll_no: {attendance_data.roll_no}")

            try:
                logger.info(f"Attempting to commit attendance record for roll_no: {attendance_data.roll_no}")
                self.db.commit()
                self.db.refresh(attendance)
                
                # Verify the record was actually saved
                verification = self.db.query(Attendance).filter(
                    Attendance.session_id == attendance_data.session_id,
                    Attendance.roll_no == attendance_data.roll_no
                ).first()
                
                if verification:
                    logger.info(f"Successfully verified attendance for roll_no: {attendance_data.roll_no}")
                    return True, "Attendance recorded successfully"
                else:
                    logger.error(f"Attendance record not found after commit for roll_no: {attendance_data.roll_no}")
                    return False, "Failed to record attendance: Database verification failed"
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Database error while saving attendance: {str(e)}")
                return False, f"Failed to record attendance: {str(e)}"

        except Exception as e:
            logger.error(f"Error in process_attendance: {str(e)}")
            return False, str(e)








