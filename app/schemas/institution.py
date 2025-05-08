from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class InstitutionBase(BaseModel):
    name: str
    city: str

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionResponse(InstitutionBase):
    id: int
    
    class Config:
        from_attributes = True

