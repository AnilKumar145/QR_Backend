from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class QRSessionBase(BaseModel):
    session_id: str
    qr_image: str
    expires_at: datetime

class QRSessionCreate(BaseModel):
    venue_id: Optional[int] = None

class QRSessionRequest(BaseModel):
    duration: int = Field(..., gt=0, le=1440, description="Duration in minutes")

class QRSessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    qr_image: str
    venue_id: Optional[int] = None
    venue_name: Optional[str] = None

    class Config:
        from_attributes = True  # new pydantic v2 syntax (previously orm_mode)

