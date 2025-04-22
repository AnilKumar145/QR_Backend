from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from . import Base

class FlaggedLog(Base):
    __tablename__ = "flagged_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String)
    reason = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FlaggedLog(session_id={self.session_id}, reason={self.reason})>"