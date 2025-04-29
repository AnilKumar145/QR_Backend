from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Dict
from datetime import datetime, timedelta
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
    existing_user = db.query(AdminUser).filter(AdminUser.username == admin_create.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    hashed_password = pwd_context.hash(admin_create.password)
    new_user = AdminUser(username=admin_create.username, hashed_password=hashed_password, is_admin=True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Admin user created successfully"}

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
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get daily counts
    daily_counts = db.query(
        func.date(Attendance.timestamp).label('date'),
        func.count().label('total'),
        func.sum(case((Attendance.is_valid_location == True, 1), else_=0)).label('valid'),
        func.sum(case((Attendance.is_valid_location == False, 1), else_=0)).label('invalid')
    ).filter(
        Attendance.timestamp.between(start_date, end_date)
    ).group_by(
        func.date(Attendance.timestamp)
    ).all()
    
    return {
        str(day.date): {
            "total": day.total,
            "valid": day.valid,
            "invalid": day.invalid
        }
        for day in daily_counts
    }

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
