from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone, UTC
from typing import Optional
import logging

from app.db.base import get_db
from app.models.qr_session import QRSession
from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from app.services.attendance_handler import AttendanceHandler
from app.core.exceptions import AttendanceException, InvalidLocationException
from app.core.config import settings
from app.services.geo_validation import GeoValidator

logger = logging.getLogger(__name__)

router = APIRouter()

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
    logger.info(f"Institution coordinates from settings: lat={settings.INSTITUTION_LAT}, lon={settings.INSTITUTION_LON}")

    try:
        # Round coordinates to 7 decimal places
        location_lat = round(float(location_lat), 7)
        location_lon = round(float(location_lon), 7)
        
        logger.info(f"Processed coordinates: lat={location_lat}, lon={location_lon}")

        # Step 1: Session validation
        qr_session = session.query(QRSession).filter_by(session_id=session_id).first()
        if not qr_session:
            logger.error(f"Session not found in database: {session_id}")
            raise HTTPException(status_code=404, detail="QR session not found")
        
        logger.info(f"Session found: {qr_session}")
        logger.info(f"Session expiry: {qr_session.expires_at}")
        
        if qr_session.is_expired():
            logger.error(f"Session expired: {session_id}")
            raise HTTPException(status_code=400, detail="QR session has expired")

        # Step 2: Duplicate check
        existing = session.query(Attendance).filter_by(
            session_id=session_id,
            roll_no=roll_no
        ).first()
        
        if existing:
            logger.error(f"Duplicate attendance for roll no {roll_no} in session {session_id}")
            raise HTTPException(
                status_code=400,
                detail="Attendance already marked for this session"
            )

        # Step 3: Coordinate validation and conversion
        try:
            # Validate decimal places before rounding
            if len(str(abs(float(location_lat))).split('.')[-1]) > 7 or \
               len(str(abs(float(location_lon))).split('.')[-1]) > 7:
                raise ValueError("Coordinates must not exceed 7 decimal places")
                
            location_lat = float(location_lat)
            location_lon = float(location_lon)
            
            # Round to 7 decimal places for consistency
            location_lat = round(location_lat, 7)
            location_lon = round(location_lon, 7)
            
            logger.info(f"Processed coordinates: lat={location_lat}, lon={location_lon}")
            
            if not (-90 <= location_lat <= 90):
                raise ValueError(f"Latitude {location_lat} out of valid range (-90 to 90)")
            if not (-180 <= location_lon <= 180):
                raise ValueError(f"Longitude {location_lon} out of valid range (-180 to 180)")
                
        except (ValueError, TypeError) as e:
            logger.error(f"Coordinate validation error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid coordinate format: {str(e)}"
            )

        # Step 4: Create attendance data
        attendance_data = AttendanceCreate(
            session_id=session_id,
            name=name,
            email=email,
            roll_no=roll_no,
            phone=phone,
            branch=branch,
            section=section,
            location_lat=location_lat,
            location_lon=location_lon
        )

        # Step 5: Process attendance
        attendance_handler = AttendanceHandler(session)
        try:
            success, message = await attendance_handler.process_attendance(
                attendance_data,
                selfie
            )
            
            if not success:
                logger.error(f"Attendance processing failed: {message}")
                raise HTTPException(status_code=400, detail=message)
                
            return {"success": True, "message": message}
            
        except InvalidLocationException as le:
            logger.error(f"Location validation failed: {str(le)}")
            raise HTTPException(
                status_code=400,
                detail=str(le)
            )
        except AttendanceException as ae:
            logger.error(f"Attendance error: {str(ae)}")
            raise HTTPException(
                status_code=400,
                detail=str(ae)
            )
        except Exception as e:
            logger.error(f"Attendance processing error: {str(e)}")
            raise HTTPException(
                status_code=400,  # Changed from 500 to 400 for client-related errors
                detail=str(e)
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in attendance marking: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
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






