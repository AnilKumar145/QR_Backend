from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    city = Column(String, nullable=False)
    
    # Relationships
    venues = relationship("Venue", back_populates="institution")
    
    def __repr__(self):
        return f"<Institution(name={self.name}, city={self.city})>"
