from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, UTC
import uuid
import qrcode
import json
import base64
import logging
from io import BytesIO
import traceback

# Import models and schemas
from app.db.base import get_db
from app.schemas.qr_session import QRSessionCreate, QRSessionResponse, QRSessionRequest
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from app.models.qr_session import QRSession
from app.models.attendance import Attendance
from app.models.venue import Venue
from app.models.flagged_log import FlaggedLog  # Add this import
from app.models.institution import Institution  # Import Institution model
from app.core.config import settings
from app.services.geo_validation import GeoValidator, InvalidLocationException


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import Column, DateTime
from app.models.attendance import Attendance
from app.db.base import get_db
from app.schemas.qr_session import QRSessionCreate, QRSessionResponse
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from app.services.qr_generator import QRGenerator
from app.models.qr_session import QRSession
import uuid
import qrcode
import json
import base64
import logging
from io import BytesIO
from app.core.config import settings
from app.services.geo_validation import GeoValidator, InvalidLocationException
from app.models.qr_session import QRSession
from app.models.qr_session import QRSession
from app.core.exceptions import (
    AttendanceException,
    SessionNotFoundException,
    SessionExpiredException,
    DuplicateAttendanceException,
    InvalidCoordinateException,
    CoordinatePrecisionException,
    InvalidFileException,
    FileSizeTooLargeException,
    FileTypeNotAllowedException
)
# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=QRSessionResponse)
def generate_qr_code(
    duration_minutes: int = Query(..., gt=0, le=1440),
    venue_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Generate QR code for attendance session
    - duration_minutes must be > 0 and <= 1440 (24 hours)
    - venue_id is optional, defaults to institution in settings if not provided
    """
    try:
        # Validate duration
        if duration_minutes <= 0:
            raise HTTPException(
                status_code=400,
                detail="Duration must be greater than 0 minutes"
            )
        if duration_minutes > 1440:  # 24 hours
            raise HTTPException(
                status_code=400,
                detail="Duration cannot exceed 24 hours"
            )
            
        # Get venue if provided
        venue = None
        venue_name = None
        if venue_id:
            venue = db.query(Venue).filter(Venue.id == venue_id).first()
            if not venue:
                raise HTTPException(
                    status_code=404,
                    detail=f"Venue with ID {venue_id} not found"
                )
            venue_name = venue.name
        else:
            # Use institution name as venue name for institution-wide QR codes
            institution = db.query(Institution).filter(Institution.id == settings.DEFAULT_INSTITUTION_ID).first()
            venue_name = f"{institution.name} (Institution-wide)" if institution else "Institution-wide"
        
        # Generate session ID and expiry time
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(UTC) + timedelta(minutes=duration_minutes)
        
        # Generate attendance URL
        attendance_url = f"{settings.FRONTEND_URL}/mark-attendance/{session_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(attendance_url)
        qr.make(fit=True)

        # Create QR image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Create QR session with explicit created_at
        db_session = QRSession(
            session_id=session_id,
            expires_at=expires_at,
            qr_image=f"data:image/png;base64,{qr_image_base64}",
            created_at=datetime.now(UTC),
            venue_id=venue_id if venue_id else None
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        # Add venue_name to response
        response_data = db_session.__dict__.copy()
        response_data["venue_name"] = venue_name
        
        return response_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate QR code: {str(e)}"
        )

@router.post("/validate", response_model=AttendanceResponse)
def validate_session(session_data: AttendanceCreate, db: Session = Depends(get_db)):
    """Validate QR session and mark attendance"""
    try:
        # First validate coordinate precision
        lat_str = str(abs(float(session_data.location_lat)))
        lon_str = str(abs(float(session_data.location_lon)))
        
        # Check decimal places
        lat_decimals = len(lat_str.split('.')[-1]) if '.' in lat_str else 0
        lon_decimals = len(lon_str.split('.')[-1]) if '.' in lon_str else 0
        
        if lat_decimals > 7 or lon_decimals > 7:
            raise CoordinatePrecisionException(lat_decimals, lon_decimals)

        # Basic range validation
        if not (-90 <= session_data.location_lat <= 90):
            raise InvalidCoordinateException(lat=session_data.location_lat)
        if not (-180 <= session_data.location_lon <= 180):
            raise InvalidCoordinateException(lon=session_data.location_lon)

        # Round coordinates to 7 decimal places
        location_lat = round(float(session_data.location_lat), 7)
        location_lon = round(float(session_data.location_lon), 7)

        # Get the session
        session = db.query(QRSession).filter_by(session_id=session_data.session_id).first()
        if not session:
            # Log the invalid session
            flagged_log = FlaggedLog(
                session_id=session_data.session_id,
                roll_no=session_data.roll_no,
                reason="Session Not Found",
                details=f"Session ID not found in database"
            )
            db.add(flagged_log)
            db.commit()
            
            raise SessionNotFoundException(session_data.session_id)
        
        # Check session expiration
        if session.is_expired():
            # Log expired session attempt
            flagged_log = FlaggedLog(
                session_id=session_data.session_id,
                roll_no=session_data.roll_no,
                reason="Expired Session",
                details=f"Attempted to use expired session. Expired at: {session.expires_at}"
            )
            db.add(flagged_log)
            db.commit()
            
            raise SessionExpiredException(str(session.expires_at))

        # Get venue if available
        venue = None
        if session.venue_id:
            venue = db.query(Venue).filter_by(id=session.venue_id).first()

        # Validate location using GeoValidator with venue if available
        geo_validator = GeoValidator(venue)
        try:
            is_valid, distance = geo_validator.is_location_valid(location_lat, location_lon)
            
            # Log the distance for debugging
            logger.info(f"Distance from venue: {distance:.2f} meters")
            
            if not is_valid:
                # Log invalid location attempt in flagged_logs
                venue_name = venue.name if venue else "campus"
                max_distance = venue.radius_meters if venue else settings.GEOFENCE_RADIUS_M
                
                flagged_log = FlaggedLog(
                    session_id=session_data.session_id,
                    roll_no=session_data.roll_no,
                    reason="Location Out of Range",
                    details=(
                        f"Distance: {distance:.0f}m from {venue_name}. "
                        f"Max allowed: {max_distance}m. "
                        f"User location: {location_lat}, {location_lon}. "
                        f"Venue location: {venue.latitude if venue else settings.INSTITUTION_LAT}, "
                        f"{venue.longitude if venue else settings.INSTITUTION_LON}"
                    )
                )
                db.add(flagged_log)
                db.commit()
                
                # Create a more detailed exception
                raise InvalidLocationException(
                    distance=distance,
                    lat=location_lat,
                    lon=location_lon,
                    venue_lat=venue.latitude if venue else settings.INSTITUTION_LAT,
                    venue_lon=venue.longitude if venue else settings.INSTITUTION_LON,
                    venue_name=venue_name,
                    max_distance=max_distance
                )

        except InvalidLocationException as e:
            raise HTTPException(
                status_code=400,
                detail=e.to_dict()
            )

        # Check for duplicate attendance
        existing_attendance = db.query(Attendance).filter_by(
            session_id=session_data.session_id,
            roll_no=session_data.roll_no
        ).first()
        
        if existing_attendance:
            # Log duplicate attendance attempt
            flagged_log = FlaggedLog(
                session_id=session_data.session_id,
                roll_no=session_data.roll_no,
                reason="Duplicate Attendance",
                details=f"Attempted to mark attendance again. Original timestamp: {existing_attendance.timestamp}"
            )
            db.add(flagged_log)
            db.commit()
            
            raise DuplicateAttendanceException(
                roll_no=session_data.roll_no,
                session_id=session_data.session_id,
                timestamp=str(existing_attendance.timestamp)
            )

        # Create attendance record with created_at field
        current_time = datetime.now(UTC)
        attendance_dict = session_data.model_dump()
        attendance_dict.update({
            'location_lat': location_lat,
            'location_lon': location_lon,
            'is_valid_location': True,
            'timestamp': current_time,
            'created_at': current_time
        })
        
        attendance = Attendance(**attendance_dict)
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        return attendance

    except (SessionNotFoundException, SessionExpiredException, 
            DuplicateAttendanceException, InvalidCoordinateException,
            CoordinatePrecisionException) as e:
        # These exceptions already have the right format
        raise e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating session: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": f"Failed to validate session: {str(e)}"
            }
        )

@pytest.mark.qr_session
def test_validate_session_invalid_data(client: TestClient):
    """Test validation with non-existent session"""
    attendance_data = {
        "session_id": "non-existent-session",
        "name": "John Doe",
        "email": "john@example.com",
        "roll_no": "12345",
        "phone": "1234567890",
        "branch": "CSE",
        "section": "A",
        "location_lat": 16.466167,
        "location_lon": 80.674499
    }
    
    response = client.post(
        "/api/v1/qr-session/validate",
        json=attendance_data
    )
    assert response.status_code == 404  # Session not found
    assert "not found" in response.json()["detail"].lower()

@router.post("/generate-for-venue/{venue_id}", response_model=QRSessionResponse)
def generate_session_for_venue(
    venue_id: int,
    request_body: QRSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a QR code session for a specific venue.
    - The duration of the session is passed in the request body.
    """
    try:
        # Fetch the venue by its ID
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if not venue:
            raise HTTPException(
                status_code=404,
                detail=f"Venue with ID {venue_id} not found"
            )

        # Use the duration from the request body
        duration_minutes = request_body.duration

        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Calculate the expiration time
        expires_at = datetime.now(UTC) + timedelta(minutes=duration_minutes)

        # Generate the attendance URL for the frontend
        attendance_url = f"{settings.FRONTEND_URL}/mark-attendance/{session_id}"

        # Generate the QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(attendance_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Create the QR session in the database
        db_session = QRSession(
            session_id=session_id,
            expires_at=expires_at,
            qr_image=f"data:image/png;base64,{qr_image_base64}",
            venue_id=venue_id
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        # Prepare and return the response
        return QRSessionResponse(
            session_id=db_session.session_id,
            created_at=db_session.created_at,
            expires_at=db_session.expires_at,
            qr_image=db_session.qr_image,
            venue_id=db_session.venue_id,
            venue_name=venue.name
        )
    except Exception as e:
        logger.error(f"Error generating QR session for venue {venue_id}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))















