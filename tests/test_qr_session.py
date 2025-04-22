import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
from app.models.qr_session import QRSession
from app.models.attendance import Attendance

@pytest.mark.qr_session
def test_generate_qr_code_success(client: TestClient, db: Session):
    """Test successful QR code generation with valid duration"""
    response = client.post("/api/v1/qr-session/generate?duration_minutes=15")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "qr_image" in data
    assert "expires_at" in data
    
    session = db.query(QRSession).filter_by(session_id=data["session_id"]).first()
    assert session is not None
    assert not session.is_expired()

@pytest.mark.qr_session
def test_generate_qr_code_invalid_duration(client: TestClient):
    """Test QR code generation with invalid duration values"""
    test_cases = [
        (-5, "Duration must be greater than 0 minutes"),
        (0, "Duration must be greater than 0 minutes"),
        (1441, "Duration cannot exceed 24 hours")
    ]
    
    for duration, expected_error in test_cases:
        response = client.post(f"/api/v1/qr-session/generate?duration_minutes={duration}")
        assert response.status_code == 400
        assert expected_error in response.json()["detail"]

@pytest.mark.qr_session
def test_validate_session_success(client: TestClient, db: Session):
    """Test successful attendance validation"""
    # Generate session
    response = client.post("/api/v1/qr-session/generate?duration_minutes=5")
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    attendance_data = {
        "name": "Test Student",
        "email": "test@example.com",
        "roll_no": "123456",
        "phone": "1234567890",
        "branch": "CSE",
        "section": "A",
        "location_lat": 16.466167,
        "location_lon": 80.674499,
        "session_id": session_id
    }
    
    response = client.post("/api/v1/qr-session/validate", json=attendance_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == attendance_data["name"]
    assert data["email"] == attendance_data["email"]

@pytest.mark.qr_session
def test_validate_expired_session(client: TestClient, db: Session):
    """Test attendance validation with expired session"""
    response = client.post("/api/v1/qr-session/generate?duration_minutes=2")
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    
    # Expire the session
    session = db.query(QRSession).filter_by(session_id=session_id).first()
    session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()
    
    attendance_data = {
        "name": "Test Student",
        "email": "test@example.com",
        "roll_no": "123456",
        "phone": "1234567890",
        "branch": "CSE",
        "section": "A",
        "location_lat": 16.466167,
        "location_lon": 80.674499,
        "session_id": session_id
    }
    
    response = client.post("/api/v1/qr-session/validate", json=attendance_data)
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

@pytest.mark.qr_session
def test_validate_nonexistent_session(client: TestClient):
    """Test attendance validation with non-existent session"""
    attendance_data = {
        "name": "Test Student",
        "email": "test@example.com",
        "roll_no": "123456",
        "phone": "1234567890",
        "branch": "CSE",
        "section": "A",
        "location_lat": 16.466167,
        "location_lon": 80.674499,
        "session_id": "nonexistent-id"
    }
    
    response = client.post("/api/v1/qr-session/validate", json=attendance_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.qr_session
def test_duplicate_attendance(client: TestClient, db: Session):
    """Test duplicate attendance submission"""
    response = client.post("/api/v1/qr-session/generate?duration_minutes=5")
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    attendance_data = {
        "name": "Test Student",
        "email": "test@example.com",
        "roll_no": "123456",
        "phone": "1234567890",
        "branch": "CSE",
        "section": "A",
        "location_lat": 16.466167,
        "location_lon": 80.674499,
        "session_id": session_id
    }
    
    # First submission
    response = client.post("/api/v1/qr-session/validate", json=attendance_data)
    assert response.status_code == 200

    # Duplicate submission
    response = client.post("/api/v1/qr-session/validate", json=attendance_data)
    assert response.status_code == 400
    assert "already marked" in response.json()["detail"].lower()

@pytest.mark.qr_session
def test_validate_session_invalid_data(client: TestClient):
    """Test validation with missing required fields"""
    # Test with missing required fields
    response = client.post(
        "/api/v1/qr-session/validate",
        json={
            "session_id": "test-session"
            # Missing other required fields
        }
    )
    assert response.status_code == 422  # Validation error
    errors = response.json()
    assert "field required" in str(errors).lower()  # Check for missing field message

@pytest.mark.qr_session
def test_validate_session_validation_error(client: TestClient, db: Session):
    """Test validation with invalid data format"""
    # First create a valid session
    response = client.post("/api/v1/qr-session/generate?duration_minutes=5")
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # Test with invalid email format
    attendance_data = {
        "session_id": session_id,  # Use valid session ID
        "name": "Test Student",
        "email": "invalid-email",  # Invalid email format
        "roll_no": "123456",
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
    assert response.status_code == 422
    errors = response.json()
    assert "email" in str(errors).lower()  # Check for email validation error

@pytest.mark.qr_session
def test_validate_nonexistent_session(client: TestClient):
    """Test validation with non-existent session"""
    attendance_data = {
        "session_id": "non-existent-session",
        "name": "Test Student",
        "email": "test@example.com",
        "roll_no": "123456",
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
    assert response.status_code == 404
    error_detail = response.json()["detail"]
    assert "not found" in error_detail.lower()










