from pydantic import BaseModel, Field, EmailStr
from typing import Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, validator
from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID
import re
class AttendanceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student")
    email: EmailStr = Field(..., description="Valid email address")
    roll_no: str = Field(..., min_length=5, max_length=20, description="Student roll number")
    phone: Annotated[str, StringConstraints(pattern=r'^\d{10,12}$')] = Field(
        ..., 
        description="Phone number (10-12 digits)"
    )
    branch: str = Field(
        ..., 
        min_length=2, 
        max_length=50,
        description="Academic branch/department"
    )
    section: str = Field(
        ..., 
        min_length=1, 
        max_length=10,
        description="Class section"
    )
    location_lat: float = Field(
        ..., 
        ge=-90, 
        le=90,
        description="Latitude coordinate"
    )
    location_lon: float = Field(
        ..., 
        ge=-180, 
        le=180,
        description="Longitude coordinate"
    )

    @validator('location_lat', 'location_lon')
    def validate_coordinate_precision(cls, v):
        # Convert to string and check decimal places
        str_val = str(abs(float(v)))
        if '.' in str_val:
            decimals = len(str_val.split('.')[-1])
            if decimals > 6:
                raise ValueError("Coordinates must not exceed 6 decimal places")
        return v

    session_id: str = Field(
        ...,
        description="QR session identifier"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "roll_no": "21B01A0123",
                "phone": "1234567890",
                "branch": "Computer Science",
                "section": "A1",
                "location_lat": 16.4663003,  # Updated example coordinate
                "location_lon": 80.6747153,  # Updated example coordinate
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    id: int
    created_at: datetime
    is_valid_location: bool
    selfie_path: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AttendanceList(BaseModel):
    """Schema for listing multiple attendance records"""
    items: list[AttendanceResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)













