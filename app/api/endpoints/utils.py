from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import os
from app.services.geo_validation import GeoValidator, InvalidLocationException
from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from app.db.base import get_db

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

@router.get("/selfie/{filename}")
async def get_selfie(filename: str):
    """Serve selfie image"""
    file_path = os.path.join(settings.SELFIE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

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

