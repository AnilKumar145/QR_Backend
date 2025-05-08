from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class VenueBase(BaseModel):
    name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(..., gt=0, le=10000)  # Maximum 10km radius

class VenueCreate(VenueBase):
    institution_id: int

class VenueResponse(VenueBase):
    id: int
    institution_id: int
    
    class Config:
        from_attributes = True
