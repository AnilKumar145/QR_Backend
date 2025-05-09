import os
import logging
import pytz
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, case, text
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

from app.db.base import get_db
from app.schemas.attendance import AttendanceResponse
from app.schemas.admin import AdminLoginResponse, AdminCreateRequest
from app.schemas.institution import InstitutionResponse, InstitutionCreate
from app.schemas.venue import VenueResponse, VenueCreate
from app.models.attendance import Attendance
from app.models.flagged_log import FlaggedLog
from app.models.admin_user import AdminUser
from app.models.institution import Institution
from app.models.venue import Venue
from app.models.qr_session import QRSession  # Import QRSession model
from app.core.dependencies import get_current_user
from app.core.security import create_access_token

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", status_code=status.HTTP_201_CREATED)
def admin_register(
    admin_create: AdminCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        existing_user = db.query(AdminUser).filter(AdminUser.username == admin_create.username).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        hashed_password = pwd_context.hash(admin_create.password)
        # Create user without email field
        new_user = AdminUser(
            username=admin_create.username, 
            hashed_password=hashed_password, 
            is_admin=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "Admin user created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating admin user: {str(e)}"
        )

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(AdminUser).filter(AdminUser.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin}
    )
    return AdminLoginResponse(access_token=access_token)

@router.get("/attendance/all", response_model=List[AttendanceResponse])
def get_all_attendances(
    skip: int = 0, 
    limit: int = 100,
    branch: str = None,
    section: str = None,
    date: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all attendance records with optional filters"""
    query = db.query(Attendance)
    
    if branch:
        query = query.filter(Attendance.branch == branch)
    if section:
        query = query.filter(Attendance.section == section)
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            query = query.filter(
                func.date(Attendance.timestamp) == date_obj.date()
            )
        except ValueError:
            pass
    
    return query.order_by(Attendance.timestamp.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()

@router.get("/statistics/daily")
def get_daily_statistics(
    days: int = Query(7, gt=0, le=30),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Get daily attendance statistics for the last n days"""
    import logging
    from datetime import timezone, datetime, timedelta
    import pytz
    
    logger = logging.getLogger(__name__)
    
    # Use IST timezone (UTC+5:30) to match the database timestamps
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Calculate date range in IST
    end_date = now
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Generating statistics from {start_date} to {end_date} (IST)")
    
    # Create a dictionary with all dates in the range, even if no attendance
    result = {}
    current_date = start_date.date()
    while current_date <= end_date.date():
        date_str = current_date.strftime("%Y-%m-%d")
        result[date_str] = {
            "total": 0,
            "valid": 0,
            "invalid": 0
        }
        current_date += timedelta(days=1)
    
    # Get daily counts
    try:
        # First, check if we have any attendance records at all
        total_records = db.query(func.count(Attendance.id)).scalar()
        logger.info(f"Total attendance records in database: {total_records}")
        
        # Get the date range of records in the database
        min_date = db.query(func.min(Attendance.timestamp)).scalar()
        max_date = db.query(func.max(Attendance.timestamp)).scalar()
        logger.info(f"Attendance records date range: {min_date} to {max_date}")
        
        # Use SQL directly to handle timezone conversion properly
        # This query extracts the date part in the database's timezone
        query = text("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total,
                SUM(CASE WHEN is_valid_location = TRUE THEN 1 ELSE 0 END) as valid,
                SUM(CASE WHEN is_valid_location = FALSE THEN 1 ELSE 0 END) as invalid
            FROM 
                attendances
            WHERE 
                timestamp >= :start_date AND timestamp <= :end_date
            GROUP BY 
                DATE(timestamp)
            ORDER BY 
                date
        """)
        
        daily_counts = db.execute(query, {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d 23:59:59")
        }).fetchall()
        
        logger.info(f"Daily counts query returned {len(daily_counts)} rows")
        
        # Fill in the actual data
        for day in daily_counts:
            date_str = day.date.strftime("%Y-%m-%d") if hasattr(day, 'date') else str(day[0])
            logger.info(f"Processing data for date: {date_str}, total: {day.total if hasattr(day, 'total') else day[1]}")
            
            if date_str in result:
                result[date_str] = {
                    "total": int(day.total if hasattr(day, 'total') else day[1]),
                    "valid": int(day.valid if hasattr(day, 'valid') else day[2] or 0),
                    "invalid": int(day.invalid if hasattr(day, 'invalid') else day[3] or 0)
                }
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    return result

@router.get("/flagged-logs")
def get_flagged_logs(
    skip: int = 0,
    limit: int = 100,
    roll_no: str = None,  # Add roll_no as an optional filter parameter
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all flagged attendance logs"""
    try:
        # Start with a base query
        query = db.query(
            FlaggedLog.id,
            FlaggedLog.session_id,
            FlaggedLog.roll_no,
            FlaggedLog.timestamp,
            FlaggedLog.reason,
            FlaggedLog.details
        )
        
        # Apply roll_no filter if provided
        if roll_no:
            query = query.filter(FlaggedLog.roll_no == roll_no)
        
        # Execute the query with ordering, offset and limit
        logs = query.order_by(FlaggedLog.timestamp.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        # Convert to dict to handle any serialization issues
        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "session_id": log.session_id,
                "roll_no": log.roll_no,
                "reason": log.reason,
                "details": log.details if hasattr(log, 'details') else "",
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            })
        
        return {"flagged_logs": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving flagged logs: {str(e)}")

@router.get("/statistics/summary")
def get_statistics_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Get summary statistics for attendance"""
    try:
        # Get total attendance count
        total_attendance = db.query(Attendance).count()
        
        # Get valid locations count
        valid_locations = db.query(Attendance).filter(Attendance.is_valid_location == True).count()
        
        # Get invalid locations count
        invalid_locations = db.query(Attendance).filter(Attendance.is_valid_location == False).count()
        
        # Get unique students count
        unique_students = db.query(Attendance.roll_no).distinct().count()
        
        # Get today's attendance count
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_attendance = db.query(Attendance).filter(Attendance.timestamp >= today_start).count()
        
        # Return the statistics
        return {
            "total_attendance": total_attendance,
            "valid_locations": valid_locations,
            "invalid_locations": invalid_locations,
            "unique_students": unique_students,
            "today_attendance": today_attendance,
            "flagged_logs": db.query(FlaggedLog).count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

# Institution endpoints
@router.post("/institutions", response_model=InstitutionResponse)
def create_institution(institution: InstitutionCreate, db: Session = Depends(get_db)):
    """Create a new institution"""
    db_institution = Institution(name=institution.name, city=institution.city)
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
    return db_institution

@router.get("/institutions", response_model=List[InstitutionResponse])
def get_institutions(db: Session = Depends(get_db)):
    """Get all institutions"""
    return db.query(Institution).all()

@router.get("/institutions/{institution_id}", response_model=InstitutionResponse)
def get_institution(institution_id: int, db: Session = Depends(get_db)):
    """Get institution by ID"""
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution

# Venue endpoints
@router.post("/venues", response_model=VenueResponse)
def create_venue(venue: VenueCreate, db: Session = Depends(get_db)):
    """Create a new venue"""
    # Check if institution exists
    institution = db.query(Institution).filter(Institution.id == venue.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    db_venue = Venue(
        institution_id=venue.institution_id,
        name=venue.name,
        latitude=venue.latitude,
        longitude=venue.longitude,
        radius_meters=venue.radius_meters
    )
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue

@router.get("/venues", response_model=List[dict])
def list_venues(db: Session = Depends(get_db)):
    """List all venues with their institution names"""
    try:
        # Use a join to get institution names
        venues_with_institutions = db.execute("""
            SELECT v.id, v.name, v.latitude, v.longitude, v.radius_meters, 
                   i.id as institution_id, i.name as institution_name
            FROM venues v
            JOIN institutions i ON v.institution_id = i.id
            ORDER BY v.name
        """).fetchall()
        
        # Convert to list of dictionaries
        result = []
        for venue in venues_with_institutions:
            result.append({
                "id": venue.id,
                "name": venue.name,
                "latitude": venue.latitude,
                "longitude": venue.longitude,
                "radius_meters": venue.radius_meters,
                "institution_id": venue.institution_id,
                "institution_name": venue.institution_name
            })
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list venues: {str(e)}"
        )

@router.get("/venues/{venue_id}", response_model=VenueResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Get venue by ID"""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue

@router.get("/venues/by-institution/{institution_id}", response_model=List[VenueResponse])
def get_venues_by_institution(
    institution_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all venues for a specific institution"""
    venues = db.query(Venue).filter(Venue.institution_id == institution_id).all()
    if not venues:
        return []
    return venues

@router.get("/statistics/by-venue/{venue_id}")
def get_venue_statistics(
    venue_id: int,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get attendance statistics for a specific venue"""
    # Check if venue exists
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get QR sessions for this venue
    sessions = db.query(QRSession).filter(
        QRSession.venue_id == venue_id,
        QRSession.created_at >= start_date,
        QRSession.created_at <= end_date
    ).all()
    
    session_ids = [session.session_id for session in sessions]
    
    # Get attendance records for these sessions
    attendance_records = db.query(Attendance).filter(
        Attendance.session_id.in_(session_ids)
    ).all()
    
    # Get flagged logs for these sessions
    flagged_logs = db.query(FlaggedLog).filter(
        FlaggedLog.session_id.in_(session_ids)
    ).all()
    
    # Organize by date
    attendance_by_date = {}
    for record in attendance_records:
        date_str = record.timestamp.strftime("%Y-%m-%d")
        if date_str not in attendance_by_date:
            attendance_by_date[date_str] = 0
        attendance_by_date[date_str] += 1
    
    # Organize flagged logs by reason
    flagged_by_reason = {}
    for log in flagged_logs:
        if log.reason not in flagged_by_reason:
            flagged_by_reason[log.reason] = 0
        flagged_by_reason[log.reason] += 1
    
    return {
        "venue": {
            "id": venue.id,
            "name": venue.name,
            "latitude": venue.latitude,
            "longitude": venue.longitude,
            "radius_meters": venue.radius_meters
        },
        "date_range": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "days": days
        },
        "sessions": {
            "total": len(sessions),
            "session_ids": session_ids
        },
        "attendance": {
            "total": len(attendance_records),
            "by_date": attendance_by_date
        },
        "flagged_logs": {
            "total": len(flagged_logs),
            "by_reason": flagged_by_reason
        }
    }



