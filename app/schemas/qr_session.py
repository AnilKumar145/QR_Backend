from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class QRSessionBase(BaseModel):
    session_id: str
    qr_image: str
    expires_at: datetime

class QRSessionCreate(QRSessionBase):
    pass

class QRSessionResponse(QRSessionBase):
    id: int
    created_at: datetime  # Make sure this is required and not Optional

    class Config:
        from_attributes = True  # new pydantic v2 syntax (previously orm_mode)


