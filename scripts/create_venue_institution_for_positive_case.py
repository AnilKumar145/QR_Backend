import os
import sys
from sqlalchemy.orm import Session
from app.db.base import SessionLocal, init_db
from app.models.institution import Institution
from app.models.venue import Venue

INSTITUTIONS = [
    {"name": "Saracity University", "city": "Hyderabad"},
    {"name": "Raj University", "city": "Mumbai"},
    {"name": "NovaTech Institute", "city": "Delhi"},
    {"name": "Crescent College", "city": "Chennai"},
    {"name": "Techverse University", "city": "Pune"},
    {"name": "CodeBridge Academy", "city": "Bangalore"},
    {"name": "Logic Valley Institute", "city": "Ahmedabad"},
    {"name": "Udaan University", "city": "Jaipur"},
    {"name": "EasternTech College", "city": "Kolkata"},
    {"name": "Kerala Institute of AI", "city": "Kochi"},
]

VENUES = [
    ("Saracity University", "IT Hall", 17.4446, 78.3498, 200),
    ("Raj University", "AI Lab", 19.0760, 72.8777, 200),
    ("NovaTech Institute", "Robotics Arena", 28.6139, 77.2090, 200),
    ("Crescent College", "Smart Class A", 13.0827, 80.2707, 200),
    ("Techverse University", "Data Center Lab", 18.5204, 73.8567, 200),
    ("CodeBridge Academy", "Seminar Hall B", 12.9716, 77.5946, 200),
    ("Logic Valley Institute", "IoT Zone", 23.0225, 72.5714, 200),
    ("Udaan University", "ML Classroom", 26.9124, 75.7873, 200),
    ("EasternTech College", "Block-C Lab", 22.5726, 88.3639, 200),
    ("Kerala Institute of AI", "Vision Lab", 9.9312, 76.2673, 200),
]

def main():
    init_db()
    db: Session = SessionLocal()
    try:
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
        print("Institutions created or found:")
        for name, id_ in name_to_id.items():
            print(f"  ID: {id_}  Name: {name}")
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
                print(f"  Venue created: {venue_name} (Institution ID: {institution_id})")
            else:
                print(f"  Venue already exists: {venue_name} (Institution ID: {institution_id})")
        print("\nInstitutions and venues created or verified successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 