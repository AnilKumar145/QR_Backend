from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, UTC
from . import Base

class QRSession(Base):
    __tablename__ = "qr_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    qr_image = Column(Text, nullable=False)

    def is_expired(self) -> bool:
        """Check if the session is expired"""
        return datetime.now(UTC) > self.expires_at

    def __repr__(self):
        return f"<QRSession(session_id={self.session_id}, expires_at={self.expires_at})>"



