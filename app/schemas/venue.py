from pydantic import BaseModel, Field
from typing import Optional

class VenueBase(BaseModel):
    name: str
    institution_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[float] = None

class VenueCreate(VenueBase):
    pass

class VenueUpdate(VenueBase):
    name: Optional[str] = None
    institution_id: Optional[int] = None

class VenueResponse(VenueBase):
    id: int
    
    class Config:
        orm_mode = True

class VenueListResponse(BaseModel):
    id: int
    name: str
    institution_name: str
    
    class Config:
        orm_mode = True

