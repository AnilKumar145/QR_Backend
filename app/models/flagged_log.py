from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

# Import Base from base_class instead of base
from app.db.base_class import Base

class FlaggedLog(Base):
    __tablename__ = "flagged_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    roll_no = Column(String, index=True)  # Added roll_no column
    timestamp = Column(DateTime(timezone=True), default=datetime.now(UTC))
    reason = Column(String)
    details = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<FlaggedLog(session_id={self.session_id}, roll_no={self.roll_no})>"



