from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, UTC

# Import Base from base_class instead of base
from app.db.base_class import Base

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
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    timestamp = Column(DateTime(timezone=True), default=datetime.now(UTC))
    selfie_path = Column(String, nullable=True)
    selfie_data = Column(LargeBinary)
    selfie_content_type = Column(String)
    
    # Add relationship to QRSession
    session = relationship("QRSession", back_populates="attendances")
    
    def __repr__(self):
        return f"<Attendance(roll_no={self.roll_no}, session_id={self.session_id})>"

















