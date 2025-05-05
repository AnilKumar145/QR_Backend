from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

# Import Base from base_class instead of base
from app.db.base_class import Base

class QRSession(Base):
    __tablename__ = "qr_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    qr_image = Column(String, nullable=False)
    
    # Add relationship to Attendance
    attendances = relationship("Attendance", back_populates="session")

    def is_expired(self) -> bool:
        """Check if the session is expired"""
        return datetime.now(UTC) > self.expires_at

    def __repr__(self):
        return f"<QRSession(session_id={self.session_id}, expires_at={self.expires_at})>"












