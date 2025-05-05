from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, Response, RedirectResponse
import os
from app.services.geo_validation import GeoValidator, InvalidLocationException
from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from app.db.base import get_db
from app.models.attendance import Attendance

# Create a database engine
DATABASE_URL = "postgresql://postgres:Anil@localhost:5432/qr_attendance"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter()

@router.get("/location/validate")
def validate_location(lat: float, lon: float):
    """Validate if location is within institution boundaries"""
    validator = GeoValidator()
    try:
        is_valid, distance = validator.is_location_valid(lat, lon)
        return {
            "is_valid": is_valid,
            "distance_meters": round(distance, 2),
            "max_allowed_distance_meters": settings.GEOFENCE_RADIUS_M,
            "your_coordinates": {
                "lat": round(lat, 7),
                "lon": round(lon, 7)
            },
            "institution_coordinates": {
                "lat": settings.INSTITUTION_LAT,
                "lon": settings.INSTITUTION_LON
            }
        }
    except InvalidLocationException as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/selfie/{roll_no}")
async def get_selfie_by_roll_no(roll_no: str, db: Session = Depends(get_db)):
    """Serve the most recent selfie for a specific roll number"""
    # Find the most recent attendance record for this roll number
    attendance = db.query(Attendance).filter(
        Attendance.roll_no == roll_no
    ).order_by(Attendance.timestamp.desc()).first()
    
    if not attendance:
        raise HTTPException(status_code=404, detail=f"No attendance record found for roll number: {roll_no}")
    
    # If we have binary data in the database, return it directly
    if attendance.selfie_data:
        return Response(
            content=attendance.selfie_data,
            media_type=attendance.selfie_content_type or "image/jpeg"
        )
    
    # If we have a Cloudinary URL, redirect to it
    if attendance.selfie_path and attendance.selfie_path.startswith('http'):
        return RedirectResponse(url=attendance.selfie_path)
    
    # Try to find the file locally
    if attendance.selfie_path:
        local_path = os.path.join(settings.STATIC_FILES_DIR, attendance.selfie_path.lstrip('/static/'))
        if os.path.exists(local_path):
            return FileResponse(local_path)
    
    # If we get here, we couldn't find the selfie
    raise HTTPException(status_code=404, detail=f"Selfie not found for roll number: {roll_no}")

@router.get("/db-test", response_model=dict)
async def test_database_connection(db: Session = Depends(get_db)):
    """Test database connection and operations"""
    try:
        # Test read operation
        result = db.execute(text("SELECT 1 as test")).fetchone()
        read_success = result.test == 1
        
        # Test write operation
        test_table_query = text("""
            CREATE TABLE IF NOT EXISTS db_test (
                id SERIAL PRIMARY KEY,
                test_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute(test_table_query)
        
        # Insert test data
        insert_query = text("""
            INSERT INTO db_test (test_value) 
            VALUES (:value) 
            RETURNING id
        """)
        result = db.execute(insert_query, {"value": f"Test at {datetime.now().isoformat()}"})
        write_id = result.scalar()
        db.commit()
        
        # Get database info
        db_info = db.execute(text("SELECT version()")).scalar()
        
        return {
            "status": "success",
            "read_test": read_success,
            "write_test": write_id is not None,
            "write_id": write_id,
            "database_info": db_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }







