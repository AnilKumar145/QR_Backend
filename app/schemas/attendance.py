from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional

class AttendanceBase(BaseModel):
    name: str
    email: EmailStr  # Change from str to EmailStr for email validation
    roll_no: str
    phone: str
    branch: str
    section: str
    location_lat: float
    location_lon: float
    session_id: str

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    id: int
    created_at: datetime
    is_valid_location: bool
    selfie_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


