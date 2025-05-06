from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

# Import Base from base_class instead of base
from app.db.base_class import Base

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<AdminUser(username={self.username})>"
