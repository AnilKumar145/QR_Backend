from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, UTC

from app.models import Base

class Attendance(Base):
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    roll_no = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    branch = Column(String, nullable=False)
    section = Column(String, nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    is_valid_location = Column(Boolean, default=False)
    session_id = Column(String, ForeignKey("qr_sessions.session_id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(UTC))
    selfie_path = Column(String, nullable=True)  # Keep existing column
    
    # Add new columns for binary storage
    selfie_data = Column(LargeBinary, nullable=True)
    selfie_content_type = Column(String, nullable=True)
    
    # Relationship
    session = relationship("QRSession", back_populates="attendances")
    
    def __repr__(self):
        return f"<Attendance(roll_no={self.roll_no}, session_id={self.session_id})>"





