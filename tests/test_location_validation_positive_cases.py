import pytest
import httpx
import itertools
import uuid
from datetime import datetime, UTC

API_URL = "http://127.0.0.1:8000/api/v1/attendance/mark"

SESSION_IDS = {
    "IT Hall": "a08e2eb5-67a4-47d2-bbe9-46cdbbad7a4b",
    "AI Lab": "b2345a6e-716d-4a3e-bc13-398c1457a510",
    "Robotics Arena": "90061b9f-799d-47cd-ad16-c22ca42d73a9",
    "Smart Class A": "4132cd8e-f641-4c36-be39-f794955f21b2",
    "Data Center Lab": "56c22c77-467d-40d4-ada2-d791effc0cfe",
    "Seminar Hall B": "67c50b4b-670b-46df-8279-48a47c4ca71f",
    "IoT Zone": "1460733a-f92e-4c6f-83c8-837758782fc3",
    "ML Classroom": "0ce287af-90fe-4756-9ff4-e46f6799b232",
    "Block-C Lab": "1f8c9594-19f5-4273-ad9f-697213028086",
    "Vision Lab": "2d82bab3-ff28-4037-ab8d-045407f90bc3",
}

roll_no_counter = itertools.count(start=2000)
phone_counter = itertools.count(start=9000000000)

def get_test_selfie():
    return b"\xff\xd8\xff\xe0" + b"0" * 1000 + b"\xff\xd9"

# (venue, venue_lat, venue_lon, student_lat, student_lon)
pos_cases = [
    ("IT Hall", 17.4446, 78.3498, 17.4447, 78.3499),
    ("AI Lab", 19.0760, 72.8777, 19.0759, 72.8776),
    ("Robotics Arena", 28.6139, 77.2090, 28.6138, 77.2088),
    ("Smart Class A", 13.0827, 80.2707, 13.0826, 80.2706),
    ("Data Center Lab", 18.5204, 73.8567, 18.5205, 73.8566),
    ("Seminar Hall B", 12.9716, 77.5946, 12.9717, 77.5947),
    ("IoT Zone", 23.0225, 72.5714, 23.0226, 72.5715),
    ("ML Classroom", 26.9124, 75.7873, 26.9123, 75.7872),
    ("Block-C Lab", 22.5726, 88.3639, 22.5727, 88.3640),
    ("Vision Lab", 9.9312, 76.2673, 9.9313, 76.2672),
]

@pytest.mark.parametrize("venue, venue_lat, venue_lon, student_lat, student_lon", pos_cases)
def test_attendance_positive_cases(venue, venue_lat, venue_lon, student_lat, student_lon):
    session_id = SESSION_IDS[venue]
    current_roll_no = f"208W1A12{next(roll_no_counter):03d}_{uuid.uuid4().hex[:6]}"
    current_phone = str(next(phone_counter))
    data = {
        "session_id": session_id,
        "name": f"Test Student {venue}",
        "email": f"test_{current_roll_no}@example.com",
        "roll_no": current_roll_no,
        "phone": current_phone,
        "branch": "IT",
        "section": "A",
        "location_lat": student_lat,
        "location_lon": student_lon,
    }
    files = {"selfie": ("selfie.jpg", get_test_selfie(), "image/jpeg")}
    response = httpx.post(API_URL, data=data, files=files)
    assert response.status_code == 200, f"Expected Marked, got {response.status_code}: {response.text}" 