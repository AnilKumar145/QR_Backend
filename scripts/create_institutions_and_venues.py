import os
import sys
from sqlalchemy.orm import Session
from app.db.base import SessionLocal, init_db
from app.models.institution import Institution
from app.models.venue import Venue

# Sample data
INSTITUTIONS = [
    {"name": "Saracity University", "city": "Hyderabad"},
    {"name": "CodeZone Institute", "city": "Bengaluru"},
    {"name": "Raj University", "city": "Mumbai"},
    {"name": "Oceanic College", "city": "Chennai"},
    {"name": "MetroTech University", "city": "Delhi"},
]

VENUES = [
    # (institution_name, venue_name, latitude, longitude, radius_meters)
    ("Saracity University", "IT Hall", 17.444, 78.3498, 200),
    ("Saracity University", "AI Lab", 17.4435, 78.3502, 200),
    ("CodeZone Institute", "ML Lab", 12.9716, 77.5946, 200),
    ("CodeZone Institute", "Seminar Hall", 12.972, 77.595, 200),
    ("Raj University", "Data Hall", 19.076, 72.8777, 200),
    ("Raj University", "Quantum Lab", 19.0755, 72.8772, 200),
    ("Oceanic College", "Robotics Hall", 13.0827, 80.2707, 200),
    ("Oceanic College", "IoT Lab", 13.083, 80.2709, 200),
    ("MetroTech University", "Smart Hall", 28.6139, 77.209, 200),
    ("MetroTech University", "Dev Arena", 28.6142, 77.2095, 200),
]

def main():
    # Initialize DB (creates tables if needed)
    init_db()
    db: Session = SessionLocal()
    try:
        # Create institutions
        name_to_id = {}
        print("Creating institutions...")
        for inst in INSTITUTIONS:
            obj = db.query(Institution).filter_by(name=inst["name"]).first()
            if not obj:
                obj = Institution(**inst)
                db.add(obj)
                db.commit()
                db.refresh(obj)
            name_to_id[inst["name"]] = obj.id
        print("Institutions created:")
        for name, id_ in name_to_id.items():
            print(f"  ID: {id_}  Name: {name}")
        # Create venues
        print("\nCreating venues...")
        for inst_name, venue_name, lat, lon, radius in VENUES:
            institution_id = name_to_id[inst_name]
            obj = db.query(Venue).filter_by(name=venue_name, institution_id=institution_id).first()
            if not obj:
                obj = Venue(
                    institution_id=institution_id,
                    name=venue_name,
                    latitude=lat,
                    longitude=lon,
                    radius_meters=radius
                )
                db.add(obj)
                db.commit()
                print(f"  Venue: {venue_name} (Institution ID: {institution_id})")
            else:
                print(f"  Venue already exists: {venue_name} (Institution ID: {institution_id})")
        print("\nInstitutions and venues created successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 