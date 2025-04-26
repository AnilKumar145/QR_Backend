from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
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

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=QRSessionResponse)
def generate_qr_code(duration_minutes: int = Query(..., gt=0, le=1440), db: Session = Depends(get_db)):
    """
    Generate QR code for attendance session
    - duration_minutes must be > 0 and <= 1440 (24 hours)
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

        session_id = str(uuid.uuid4())
        expires_at = datetime.now(UTC) + timedelta(minutes=duration_minutes)
        
        # Use the FRONTEND_URL from settings
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
        
        db_session = QRSession(
            session_id=session_id,
            expires_at=expires_at,
            qr_image=f"data:image/png;base64,{qr_image_base64}"
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return db_session
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
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
        
        if lat_decimals > 6 or lon_decimals > 6:
            raise HTTPException(
                status_code=400,
                detail=f"Coordinates must not exceed 6 decimal places. Got lat:{lat_decimals}, lon:{lon_decimals} decimals"
            )

        # Round coordinates to 6 decimal places
        location_lat = round(float(session_data.location_lat), 6)
        location_lon = round(float(session_data.location_lon), 6)

        # Validate location using GeoValidator
        geo_validator = GeoValidator()
        try:
            is_valid, distance = geo_validator.is_location_valid(location_lat, location_lon)
            
            # Log the distance for debugging
            logger.info(f"Distance from institution: {distance:.2f} meters")
            
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Location out of range",
                        "message": f"You are {distance:.0f} meters away from campus. Maximum allowed distance is 500 meters.",
                        "your_location": {
                            "lat": location_lat,
                            "lon": location_lon
                        },
                        "institution_location": {
                            "lat": settings.INSTITUTION_LAT,
                            "lon": settings.INSTITUTION_LON
                        },
                        "distance": round(distance),
                        "max_allowed_distance": settings.GEOFENCE_RADIUS_M
                    }
                )

        except InvalidLocationException as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        # Continue with session validation and attendance marking...
        # Basic coordinate validation
        if not (-90 <= location_lat <= 90) or not (-180 <= location_lon <= 180):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinate values"
            )
            
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid coordinate format"
        )

    # Get the session
    session = db.query(QRSession).filter_by(session_id=session_data.session_id).first()
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    # Check session expiration
    if session.is_expired():
        raise HTTPException(
            status_code=400,
            detail="Session has expired"
        )

    # Check for duplicate attendance
    existing_attendance = db.query(Attendance).filter_by(
        session_id=session_data.session_id,
        roll_no=session_data.roll_no
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=400,
            detail="Attendance already marked for this session"
        )

    # Validate location using GeoValidator
    geo_validator = GeoValidator()
    try:
        is_valid, distance = geo_validator.is_location_valid(location_lat, location_lon)
        
        # We'll never reach here if location is invalid because is_location_valid will raise an exception
        attendance_dict = session_data.model_dump()
        attendance_dict.update({
            'location_lat': location_lat,
            'location_lon': location_lon,
            'is_valid_location': True,
            'timestamp': datetime.now(UTC)
        })
        
        attendance = Attendance(**attendance_dict)
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        return attendance

    except InvalidLocationException as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
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




























