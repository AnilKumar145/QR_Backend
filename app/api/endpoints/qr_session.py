from fastapi import APIRouter, Depends, HTTPException
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
from io import BytesIO
from app.core.config import settings

router = APIRouter()

@router.post("/generate", response_model=QRSessionResponse)
def generate_qr_code(duration_minutes: int = 2, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    expires_at = datetime.now(UTC) + timedelta(minutes=duration_minutes)
    
    # Generate direct URL QR code with HTTPS Vercel URL
    attendance_url = f"https://qr-frontend-gmx7-anilkumar145s-projects.vercel.app/mark-attendance/{session_id}"
    
    print("Debug - Attendance URL:", attendance_url)  # Debug line
    
    # Generate QR code with direct URL
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
    
    # Convert to base64
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Create DB session
    db_session = QRSession(
        session_id=session_id,
        expires_at=expires_at,
        qr_image=f"data:image/png;base64,{qr_image_base64}"
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.post("/validate", response_model=AttendanceResponse)
def validate_session(session_data: AttendanceCreate, db: Session = Depends(get_db)):
    """Validate QR session and mark attendance"""
    # Get the session
    session = db.query(QRSession).filter_by(session_id=session_data.session_id).first()
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
    existing_attendance = db.query(Attendance).filter_by(
        session_id=session_data.session_id,
        roll_no=session_data.roll_no
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=400,
            detail="Attendance already marked for this session"
        )
    
    # Create new attendance record
    attendance = Attendance(**session_data.model_dump())
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return attendance

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














