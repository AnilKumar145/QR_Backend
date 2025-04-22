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
    INSTITUTION_LAT: float = 16.466167  # KL University coordinates
    INSTITUTION_LON: float = 80.674499  # KL University coordinates
    GEOFENCE_RADIUS_KM: float = 0.05  # 50 meters radius
    
    # File storage settings
    STATIC_FILES_DIR: str = "static"
    SELFIE_DIR: str = "static/selfies"
    MAX_SELFIE_SIZE: int = 5_242_880  # 5MB in bytes
    
    # Frontend URL configuration
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # This will ignore any extra fields in the .env file

settings = Settings()

