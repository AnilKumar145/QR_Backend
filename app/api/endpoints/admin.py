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
from app.models.attendance import Attendance
from app.models.flagged_log import FlaggedLog
from app.models.admin_user import AdminUser
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all flagged attendance logs"""
    logs = db.query(FlaggedLog)\
        .order_by(FlaggedLog.timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return logs

@router.get("/statistics/summary")
def get_statistics_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Get summary statistics for attendance"""
    import logging
    from datetime import timezone, datetime, timedelta
    import pytz
    
    logger = logging.getLogger(__name__)
    
    try:
        # Use IST timezone (UTC+5:30) to match the database timestamps
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        today = now.date()
        
        # Get total counts
        total_attendance = db.query(func.count(Attendance.id)).scalar() or 0
        valid_locations = db.query(func.count(Attendance.id)).filter(Attendance.is_valid_location == True).scalar() or 0
        invalid_locations = db.query(func.count(Attendance.id)).filter(Attendance.is_valid_location == False).scalar() or 0
        
        # Get today's counts using SQL with proper timezone handling
        query = text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_valid_location = TRUE THEN 1 ELSE 0 END) as valid,
                SUM(CASE WHEN is_valid_location = FALSE THEN 1 ELSE 0 END) as invalid
            FROM 
                attendances
            WHERE 
                DATE(timestamp) = :today
        """)
        
        today_result = db.execute(query, {"today": today.strftime("%Y-%m-%d")}).fetchone()
        
        today_attendance = today_result[0] or 0
        today_valid = today_result[1] or 0
        today_invalid = today_result[2] or 0
        
        # Get unique students count
        unique_students = db.query(func.count(func.distinct(Attendance.roll_no))).scalar() or 0
        
        return {
            "total": {
                "attendance": total_attendance,
                "valid_locations": valid_locations,
                "invalid_locations": invalid_locations,
                "unique_students": unique_students
            },
            "today": {
                "attendance": today_attendance,
                "valid_locations": today_valid,
                "invalid_locations": today_invalid
            }
        }
    except Exception as e:
        logger.error(f"Error getting summary statistics: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "total": {
                "attendance": 0,
                "valid_locations": 0,
                "invalid_locations": 0,
                "unique_students": 0
            },
            "today": {
                "attendance": 0,
                "valid_locations": 0,
                "invalid_locations": 0
            }
        }


