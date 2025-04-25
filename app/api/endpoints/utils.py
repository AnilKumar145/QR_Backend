from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.services.geo_validation import GeoValidator, InvalidLocationException
from app.core.config import settings

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

