from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone, UTC
from typing import Optional
import logging
import os
import traceback
from app.db.base import get_db, SessionLocal
from app.models.qr_session import QRSession
from app.models.attendance import Attendance
from app.models.venue import Venue
from app.models.flagged_log import FlaggedLog
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from app.services.attendance_handler import AttendanceHandler
from app.core.exceptions import (
    AttendanceException,
    InvalidLocationException,
    SessionNotFoundException,
    SessionExpiredException,
    DuplicateAttendanceException,
    InvalidCoordinateException,
    CoordinatePrecisionException,
    InvalidFileException,
    FileSizeTooLargeException,
    FileTypeNotAllowedException
)
from app.core.config import settings
from app.services.geo_validation import GeoValidator

logger = logging.getLogger(__name__)

router = APIRouter()

def log_failed_attempt(log_data: dict):
    """
    Logs a failed attendance attempt in a separate database session
    to ensure it's saved even if the main transaction is rolled back.
    """
    db_log = None
    try:
        db_log = SessionLocal()
        flagged_log = FlaggedLog(**log_data)
        db_log.add(flagged_log)
        db_log.commit()
        logger.info(f"Successfully logged failed attempt for roll_no: {log_data.get('roll_no')}")
    except Exception as e:
        # --- START AGGRESSIVE DEBUGGING ---
        # Make the error extremely visible in the server logs
        print("---!!! CRITICAL ERROR WRITING TO FLAGGED LOGS !!!---")
        import traceback
        traceback.print_exc()
        print(f"---!!! LOGGING ERROR DETAILS: {e} !!!---")
        # --- END AGGRESSIVE DEBUGGING ---
        
        logger.error(f"Critical error writing to flagged_logs: {e}")
        if db_log:
            db_log.rollback()
    finally:
        if db_log:
            db_log.close()

@router.get("/selfie/{attendance_id}")
async def get_selfie(
    attendance_id: int,
    db: Session = Depends(get_db)
):
    # Get the attendance record
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Check if selfie data exists in database
    if attendance.selfie_data:
        return Response(
            content=attendance.selfie_data,
            media_type=attendance.selfie_content_type or "image/jpeg"
        )
    
    # Fall back to file system if database data doesn't exist
    if attendance.selfie_path:
        try:
            file_path = os.path.join(settings.STATIC_FILES_DIR, attendance.selfie_path.lstrip('/static/'))
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    content = f.read()
                return Response(
                    content=content,
                    media_type="image/jpeg"
                )
        except Exception:
            pass
    
    raise HTTPException(status_code=404, detail="Selfie not found")

@router.post("/mark", response_model=dict)
async def mark_attendance(
    session_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    roll_no: str = Form(...),
    phone: str = Form(...),
    branch: str = Form(...),
    section: str = Form(...),
    location_lat: float = Form(...),
    location_lon: float = Form(...),
    selfie: UploadFile = File(...),
    session: Session = Depends(get_db)
):
    logger.info(f"\n=== Starting attendance marking process for session {session_id} ===")
    logger.info(f"Raw coordinates received: lat={location_lat} ({type(location_lat)}), lon={location_lon} ({type(location_lon)})")

    try:
        # Validate file size
        selfie_content = await selfie.read()
        selfie_size = len(selfie_content)
        await selfie.seek(0)  # Reset file position
        
        if selfie_size > settings.MAX_SELFIE_SIZE:
            raise FileSizeTooLargeException(selfie_size, settings.MAX_SELFIE_SIZE)
            
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        if selfie.content_type not in allowed_types:
            raise FileTypeNotAllowedException(selfie.content_type, allowed_types)

        # Validate coordinate precision
        lat_str = str(abs(float(location_lat)))
        lon_str = str(abs(float(location_lon)))
        
        lat_decimals = len(lat_str.split('.')[-1]) if '.' in lat_str else 0
        lon_decimals = len(lon_str.split('.')[-1]) if '.' in lon_str else 0
        
        if lat_decimals > 7 or lon_decimals > 7:
            raise CoordinatePrecisionException(lat_decimals, lon_decimals)

        # Basic range validation
        if not (-90 <= location_lat <= 90):
            raise InvalidCoordinateException(lat=location_lat)
        if not (-180 <= location_lon <= 180):
            raise InvalidCoordinateException(lon=location_lon)

        # Round coordinates to 7 decimal places
        location_lat = round(float(location_lat), 7)
        location_lon = round(float(location_lon), 7)
        
        logger.info(f"Processed coordinates: lat={location_lat}, lon={location_lon}")

        # OPTIMIZATION: Use a single query with joins to get session and venue data
        from sqlalchemy.orm import joinedload
        
        qr_session = session.query(QRSession).options(
            joinedload(QRSession.venue)
        ).filter_by(session_id=session_id).first()
        
        if not qr_session:
            logger.error(f"Session not found in database: {session_id}")
            log_failed_attempt({
                "session_id": session_id, "roll_no": roll_no,
                "reason": "Session Not Found", "details": "Session ID not found in database"
            })
            raise SessionNotFoundException(session_id)
        
        logger.info(f"Session found: {qr_session}")
        logger.info(f"Session expiry: {qr_session.expires_at}")
        
        if qr_session.is_expired():
            logger.error(f"Session expired: {session_id}")
            log_failed_attempt({
                "session_id": session_id, "roll_no": roll_no,
                "reason": "Expired Session",
                "details": f"Attempted to use expired session. Expired at: {qr_session.expires_at}"
            })
            raise SessionExpiredException(str(qr_session.expires_at))

        # OPTIMIZATION: Use EXISTS for faster duplicate check
        existing = session.query(Attendance).filter(
            Attendance.session_id == session_id,
            Attendance.roll_no == roll_no
        ).first()
        
        if existing:
            logger.error(f"Duplicate attendance for roll no {roll_no} in session {session_id}")
            log_failed_attempt({
                "session_id": session_id, "roll_no": roll_no,
                "reason": "Duplicate Attendance",
                "details": f"Attempted to mark attendance again. Original timestamp: {existing.timestamp}"
            })
            raise DuplicateAttendanceException(
                roll_no=roll_no,
                session_id=session_id,
                timestamp=str(existing.timestamp)
            )

        # Step 3: Get venue for location validation (already loaded with session)
        venue = qr_session.venue
        logger.info(f"Using venue for validation: {venue.name if venue else 'None'}")
        
        # Step 4: Validate location
        geo_validator = GeoValidator(venue)
        is_valid, distance = geo_validator.is_location_valid(location_lat, location_lon)
        logger.info(f"Location validation result: valid={is_valid}, distance={distance:.2f}m")
        
        if not is_valid:
            venue_name = venue.name if venue else "campus"
            max_distance = venue.radius_meters if venue else settings.GEOFENCE_RADIUS_M

            # --- START SIMPLIFIED FIX ---
            # 1. Construct the error detail dictionary directly
            error_detail = {
                "error": "invalid_location",
                "message": "You are outside the allowed geofence.",
                "distance_meters": round(distance, 2),
                "max_distance_meters": round(max_distance, 2),
                "user_location": {"lat": location_lat, "lon": location_lon},
                "venue_name": venue_name,
                "venue_location": {
                    "lat": venue.latitude if venue else settings.INSTITUTION_LAT,
                    "lon": venue.longitude if venue else settings.INSTITUTION_LON
                }
            }

            # 2. Log the failure using the robust, independent logger
            log_failed_attempt({
                "session_id": session_id,
                "roll_no": roll_no,
                "reason": "Location Out of Range",
                "details": f"User was {distance:.2f}m away from '{venue_name}'. Max distance is {max_distance}m."
            })

            # 3. Raise the standard HTTPException
            raise HTTPException(
                status_code=400,
                detail=error_detail
            )
            # --- END SIMPLIFIED FIX ---

        # Step 6: Create attendance data
        attendance_data = AttendanceCreate(
            session_id=session_id,
            name=name,
            email=email,
            roll_no=roll_no,
            phone=phone,
            branch=branch,
            section=section,
            location_lat=location_lat,
            location_lon=location_lon,
            venue_id=qr_session.venue_id
        )

        # Step 7: Process attendance
        attendance_handler = AttendanceHandler(session)
        try:
            success, message = await attendance_handler.process_attendance(
                attendance_data,
                selfie
            )
            
            if not success:
                logger.error(f"Attendance processing failed: {message}")
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "error": "attendance_processing_failed",
                        "message": message
                    }
                )
                
            return {"success": True, "message": message}
            
        except InvalidLocationException as le:
            logger.error(f"Location validation failed: {str(le)}")
            raise HTTPException(
                status_code=400,
                detail=le.to_dict()
            )
        except AttendanceException as ae:
            logger.error(f"Attendance error: {str(ae)}")
            raise ae
        except Exception as e:
            logger.error(f"Attendance processing error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "attendance_processing_error",
                    "message": str(e)
                }
            )
            
    except (SessionNotFoundException, SessionExpiredException, 
            DuplicateAttendanceException, InvalidCoordinateException,
            CoordinatePrecisionException, FileSizeTooLargeException,
            FileTypeNotAllowedException) as e:
        # These exceptions already have the right format
        raise e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in attendance marking: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": f"Unexpected error: {str(e)}"
            }
        )

@router.post("/validate", response_model=AttendanceResponse)
def validate_session(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db)
):
    """Validate QR session and mark attendance"""
    geo_validator = GeoValidator()
    
    try:
        # Validate location first
        is_valid_location, distance = geo_validator.is_location_valid(
            attendance_data.location_lat,
            attendance_data.location_lon
        )
        
        if not is_valid_location:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid location. You are {distance:.0f}m away from the institution."
            )

        # Get the session
        session = db.query(QRSession).filter_by(
            session_id=attendance_data.session_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        # Check if session is expired
        if session.is_expired():
            raise HTTPException(
                status_code=400,
                detail="Session has expired"
            )

        # Check for duplicate attendance
        existing = db.query(Attendance).filter_by(
            session_id=attendance_data.session_id,
            roll_no=attendance_data.roll_no
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Attendance already marked for this session"
            )

        # Create new attendance record
        new_attendance = Attendance(**attendance_data.dict())
        db.add(new_attendance)
        db.commit()
        
        return {"message": "Attendance marked successfully"}
        
    except InvalidLocationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


























