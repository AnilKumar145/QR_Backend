from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.services.geo_validation import GeoValidator
from app.core.config import settings

router = APIRouter()

@router.get("/location/validate")
def validate_location(lat: float, lon: float):
    """Validate if location is within institution boundaries"""
    validator = GeoValidator()
    is_valid, distance = validator.is_location_valid(lat, lon)
    return {
        "is_valid": is_valid,
        "distance_km": round(distance, 2),
        "max_allowed_distance_km": settings.GEOFENCE_RADIUS_KM
    }

@router.get("/selfie/{filename}")
async def get_selfie(filename: str):
    """Serve selfie image"""
    file_path = os.path.join(settings.SELFIE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)