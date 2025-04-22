from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone, UTC

from app.db.base import get_db
from app.models.qr_session import QRSession
from app.schemas.attendance import AttendanceCreate, AttendanceResponse

router = APIRouter()

@router.post("/mark", response_model=AttendanceResponse, status_code=201)
def mark_attendance(attendance: AttendanceCreate, db: Session = Depends(get_db)):
    # Check if session exists and is not expired
    session = db.query(QRSession).filter_by(session_id=attendance.session_id).first()
    if not session or session.is_expired():
        raise HTTPException(
            status_code=400,
            detail="QR session has expired or is invalid"
        )
    
    # Rest of your attendance marking logic here
    ...






