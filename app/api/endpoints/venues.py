from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# Fix the import to use the correct path
from app.db.base import get_db  # Changed from app.db.session
from app.models.venue import Venue
from app.schemas.venue import VenueResponse, VenueListResponse

router = APIRouter()

@router.get("/list", response_model=List[VenueListResponse])
def list_venues(db: Session = Depends(get_db)):
    """
    List all venues with their institution names for the frontend dropdown
    """
    try:
        # Import text from sqlalchemy
        from sqlalchemy import text
        
        # Query venues with institution names using a join with text()
        sql_query = text("""
            SELECT v.id, v.name, i.name as institution_name
            FROM venues v
            JOIN institutions i ON v.institution_id = i.id
            ORDER BY v.name
        """)
        
        venues = db.execute(sql_query).fetchall()
        
        # Convert to list of dictionaries
        result = [
            {"id": venue.id, "name": venue.name, "institution_name": venue.institution_name}
            for venue in venues
        ]
        
        # Log the result for debugging
        print(f"Venues list API returned {len(result)} venues")
        
        return result
    except Exception as e:
        # Log the error for debugging
        print(f"Error in list_venues: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list venues: {str(e)}"
        )



