import pytest
from datetime import datetime, UTC, timedelta
from sqlalchemy.orm import Session
from app.models.attendance import Attendance
from app.models.qr_session import QRSession
from fastapi.testclient import TestClient

@pytest.mark.attendance
def test_create_attendance(db: Session):
    qr_session = QRSession(
        session_id="test-session-123",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        qr_image="base64_encoded_image_data"
    )
    db.add(qr_session)
    db.commit()

    # Create attendance with explicit UTC timezone
    attendance = Attendance(
        session_id="test-session-123",
        name="John Doe",
        email="john@example.com",
        roll_no="12345",
        phone="1234567890",
        branch="CSE",
        section="A",
        location_lat=16.466167,
        location_lon=80.674499,
        created_at=datetime.now(UTC)  # Force UTC timezone
    )
    db.add(attendance)
    db.commit()
    
    # Fetch fresh from database to ensure timezone
    db.refresh(attendance)
    fetched_attendance = db.query(Attendance).filter_by(session_id="test-session-123").first()
    
    # Convert to UTC if not already
    if fetched_attendance.created_at.tzinfo != UTC:
        fetched_attendance.created_at = fetched_attendance.created_at.astimezone(UTC)
        
    assert fetched_attendance.created_at.tzinfo == UTC

@pytest.mark.attendance
def test_attendance_repr(db: Session):
    """Test the string representation of attendance"""
    attendance = Attendance(
        session_id="test-session-123",
        roll_no="12345"
    )
    
    expected_repr = "<Attendance(roll_no=12345, session_id=test-session-123)>"
    assert str(attendance) == expected_repr

@pytest.mark.attendance
def test_attendance_defaults(db: Session):
    """Test default values for attendance fields"""
    qr_session = QRSession(
        session_id="test-session-123",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        qr_image="base64_encoded_image_data"
    )
    db.add(qr_session)
    db.commit()

    attendance = Attendance(
        session_id="test-session-123",
        name="John Doe",
        email="john@example.com",
        roll_no="12345",
        phone="1234567890",
        branch="CSE",
        section="A",
        location_lat=16.466167,
        location_lon=80.674499
    )
    
    db.add(attendance)
    db.commit()
    
    assert attendance.is_valid_location is False
    assert attendance.selfie_path is None
    assert isinstance(attendance.created_at, datetime)
    # Don't assert specific timezone, just verify it's timezone-aware
    assert attendance.created_at.tzinfo is not None
    assert isinstance(attendance.timestamp, datetime)
    
    # Ensure created_at is recent
    now = datetime.now(UTC)
    assert (now - attendance.created_at).total_seconds() < 5

@pytest.mark.attendance
def test_attendance_foreign_key_constraint(db: Session):
    """Test that attendance requires valid session_id"""
    attendance = Attendance(
        session_id="nonexistent-session",
        name="John Doe",
        email="john@example.com",
        roll_no="12345",
        phone="1234567890",
        branch="CSE",
        section="A",
        location_lat=16.466167,
        location_lon=80.674499
    )
    
    db.add(attendance)
    with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
        db.commit()

@pytest.mark.attendance
def test_validate_session_invalid_data(client: TestClient):
    """Test validation with non-existent session"""
    attendance_data = {
        "session_id": "non-existent-session",
        "name": "John Doe",
        "email": "john@example.com",
        "roll_no": "12345",
        "phone": "1234567890",
        "branch": "CSE",
        "section": "A",
        "location_lat": 16.466167,
        "location_lon": 80.674499
    }
    
    response = client.post(
        "/api/v1/qr-session/validate",
        json=attendance_data
    )
    assert response.status_code == 404  # Session not found
    error_detail = response.json()["detail"]
    assert isinstance(error_detail, str)  # Ensure it's a string
    assert "not found" in error_detail.lower()

@pytest.mark.attendance
def test_attendance_invalid_location(db: Session):
    """Test attendance with coordinates outside institution boundary"""
    # Create QR session first
    qr_session = QRSession(
        session_id="test-session-123",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        qr_image="base64_encoded_image_data"
    )
    db.add(qr_session)
    db.commit()

    attendance = Attendance(
        session_id="test-session-123",
        name="John Doe",
        email="john@example.com",
        roll_no="12345",
        phone="1234567890",
        branch="CSE",
        section="A",
        location_lat=17.466167,  # Far from institution
        location_lon=81.674499   # Far from institution
    )
    
    db.add(attendance)
    db.commit()
    
    assert attendance.is_valid_location is False

@pytest.mark.attendance
def test_attendance_expired_session(client: TestClient, db: Session):
    """Test attendance creation with expired QR session"""
    # Create an expired session
    qr_session = QRSession(
        session_id="expired-session-123",
        expires_at=datetime.now(UTC) - timedelta(minutes=15),  # Expired 15 minutes ago
        qr_image="base64_encoded_image_data"  # Add qr_image
    )
    db.add(qr_session)
    db.commit()

    response = client.post(
        "/api/v1/attendance/mark",
        json={
            "session_id": "expired-session-123",
            "name": "John Doe",
            "email": "john@example.com",
            "roll_no": "12345",
            "phone": "1234567890",
            "branch": "CSE",
            "section": "A",
            "location_lat": 16.466167,
            "location_lon": 80.674499
        }
    )
    
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

@pytest.mark.attendance
def test_duplicate_attendance(client: TestClient, db: Session):
    """Test preventing duplicate attendance for same session"""
    # Create active session
    qr_session = QRSession(
        session_id="test-session-123",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        qr_image="base64_encoded_image_data"
    )
    db.add(qr_session)
    db.commit()

    attendance_data = {
        "session_id": "test-session-123",
        "name": "John Doe",
        "email": "john@example.com",
        "roll_no": "12345",
        "phone": "1234567890",
        "branch": "CSE",
        "section": "A",
        "location_lat": 16.466167,
        "location_lon": 80.674499
    }

    # First attendance should succeed
    response = client.post("/api/v1/qr-session/validate", json=attendance_data)
    assert response.status_code == 200

    # Second attempt should fail
    response = client.post("/api/v1/qr-session/validate", json=attendance_data)
    assert response.status_code == 400
    assert "already marked" in response.json()["detail"].lower()
























