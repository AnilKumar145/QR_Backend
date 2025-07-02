from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "QR Attendance System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str
    
    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Institution settings
    INSTITUTION_LAT: float = 16.4663  # Institution's latitude
    INSTITUTION_LON: float = 80.6747  # Institution's longitude
    GEOFENCE_RADIUS_M: float = 500.0  # 500 meters radius for geofencing
    
    # File storage settings
    STATIC_FILES_DIR: str = "static"
    SELFIE_DIR: str = "static/selfies"
    MAX_SELFIE_SIZE: int = 5_242_880  # 5MB in bytes
    
    # Frontend URL configuration
    FRONTEND_URL: str = "https://new-attendance-form.vercel.app"  # Update with your actual Render URL

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # This will ignore any extra fields in the .env file

settings = Settings()


