from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False)

    institution = relationship("Institution", back_populates="venues")
    qr_sessions = relationship("QRSession", back_populates="venue")

    def __repr__(self):
        return f"<Venue(name={self.name}, institution_id={self.institution_id})>"
