from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone, UTC
import logging

from app.db.base import get_db
from app.models.qr_session import QRSession
from app.schemas.attendance import AttendanceCreate, AttendanceResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/mark")
async def mark_attendance(
    attendance_data: AttendanceCreate,
    session: Session = Depends(get_db)
):
    try:
        # Add logging to debug
        logger.info(f"Received attendance data: {attendance_data}")
        
        # Check if session exists and is not expired
        qr_session = session.query(QRSession).filter_by(session_id=attendance_data.session_id).first()
        if not qr_session or qr_session.is_expired():
            raise HTTPException(
                status_code=400,
                detail="QR session has expired or is invalid"
            )
        
        # Rest of your attendance marking logic here
        # For now, we'll just return a success message
        return {"message": "Attendance marked successfully"}
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error marking attendance: {str(e)}"
        )








