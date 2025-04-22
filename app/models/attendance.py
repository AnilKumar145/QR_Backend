from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from datetime import datetime, UTC
from . import Base

class Attendance(Base):
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("qr_sessions.session_id"))
    name = Column(String)
    email = Column(String)
    roll_no = Column(String)
    phone = Column(String)
    branch = Column(String)
    section = Column(String)
    location_lat = Column(Float)
    location_lon = Column(Float)
    selfie_path = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))  # Update this too for consistency
    is_valid_location = Column(Boolean, default=False)
    

    def __repr__(self):
        return f"<Attendance(roll_no={self.roll_no}, session_id={self.session_id})>"


