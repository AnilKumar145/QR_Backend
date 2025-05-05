from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime, UTC
class QRSession(Base):
    __tablename__ = "qr_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    qr_image = Column(String)
    
    # Fix the relationship name to match what's in Attendance model
    attendances = relationship("Attendance", back_populates="session")

    def is_expired(self) -> bool:
        """Check if the session is expired"""
        return datetime.now(UTC) > self.expires_at

    def __repr__(self):
        return f"<QRSession(session_id={self.session_id}, expires_at={self.expires_at})>"






