from pydantic import BaseModel, Field, EmailStr
from typing import Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, validator
from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID
import re
class AttendanceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(...)
    roll_no: str = Field(..., min_length=5, max_length=20)
    phone: Annotated[str, StringConstraints(pattern=r'^\d{10,12}$')] = Field(...)
    branch: str = Field(..., min_length=2, max_length=50)
    section: str = Field(..., min_length=1, max_length=10)
    location_lat: float = Field(..., ge=-90, le=90)
    location_lon: float = Field(..., ge=-180, le=180)
    session_id: str = Field(...)
    venue_id: Optional[int] = Field(None)  # Add venue_id field

    @validator('location_lat', 'location_lon')
    def validate_coordinate_precision(cls, v):
        # Convert to string and check decimal places
        str_val = str(abs(float(v)))
        if '.' in str_val:
            decimals = len(str_val.split('.')[-1])
            if decimals > 7:
                raise ValueError("Coordinates must not exceed 7 decimal places")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "roll_no": "21B01A0123",
                "phone": "1234567890",
                "branch": "Computer Science",
                "section": "A1",
                "location_lat": 16.4663003,
                "location_lon": 80.6747153,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "venue_id": 1
            }
        }

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    id: int
    is_valid_location: bool
    timestamp: datetime
    created_at: datetime  # This field is required in the response

    class Config:
        from_attributes = True

class AttendanceList(BaseModel):
    """Schema for listing multiple attendance records"""
    items: list[AttendanceResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)















