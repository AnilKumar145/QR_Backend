from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class QRSessionBase(BaseModel):
    session_id: str

class QRSessionCreate(QRSessionBase):
    expires_at: datetime

class QRSessionResponse(QRSessionBase):
    id: int
    created_at: datetime
    expires_at: datetime
    qr_image: str  # base64 encoded image

    class Config:
        from_attributes = True  # new pydantic v2 syntax (previously orm_mode)
