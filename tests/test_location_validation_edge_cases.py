import pytest
import httpx
import itertools

API_URL = "http://127.0.0.1:8000/api/v1/attendance/mark"

SESSION_IDS = {
    "IT Hall": "516d14e5-d0f8-45b9-8c5f-56ece9191e03",
    "AI Lab": "ca2d590b-8566-40c9-a3bb-ed23102beb0e",
    "Robotics Arena": "2a1f7e6a-18c9-4c78-bd64-a93de63e0979",
    "Smart Class A": "64883f55-80eb-4810-bde4-11a6532937db",
    "Data Center Lab": "dfdcb025-6080-4dde-9d98-1d245af04531",
    "Seminar Hall B": "36c12763-137a-4564-b117-8f8cef1c1186",
    "IoT Zone": "d14e422a-9d29-4b0e-a904-cf73bca5e21e",
    "ML Classroom": "6d1dd2d8-17c8-4f14-8e66-a11da284f812",
    "Block-C Lab": "beb32753-0ad8-4544-9aa1-813e8fde6fbc",
    "Vision Lab": "af488337-c8af-42e5-9a15-4c1c6e9cc368",
}

roll_no_counter = itertools.count(start=7000)

def get_test_selfie():
    return b"\xff\xd8\xff\xe0" + b"0" * 1000 + b"\xff\xd9"

# (venue, venue_lat, venue_lon, student_lat, student_lon)
edge_cases = [
    ("IT Hall", 17.4446, 78.3498, 17.4449, 78.3502),
    ("AI Lab", 19.0760, 72.8777, 19.0750, 72.8770),
    ("Robotics Arena", 28.6139, 77.2090, 28.6128, 77.2081),
    ("Smart Class A", 13.0827, 80.2707, 13.0835, 80.2715),
    ("Data Center Lab", 18.5204, 73.8567, 18.5209, 73.8571),
    ("Seminar Hall B", 12.9716, 77.5946, 12.9722, 77.5953),
    ("IoT Zone", 23.0225, 72.5714, 23.0234, 72.5723),
    ("ML Classroom", 26.9124, 75.7873, 26.9115, 75.7865),
    ("Block-C Lab", 22.5726, 88.3639, 22.5718, 88.3630),
    ("Vision Lab", 9.9312, 76.2673, 9.9303, 76.2665),
]

@pytest.mark.parametrize("venue, venue_lat, venue_lon, student_lat, student_lon", edge_cases)
def test_attendance_edge_cases(venue, venue_lat, venue_lon, student_lat, student_lon):
    session_id = SESSION_IDS[venue]
    roll_num_part = next(roll_no_counter)
    current_roll_no = f"208W1A12{roll_num_part:04d}"
    current_phone = f"98765{roll_num_part:05d}"

    data = {
        "session_id": session_id,
        "name": f"Test Student {current_roll_no}",
        "email": f"test_{current_roll_no}@example.com",
        "roll_no": current_roll_no,
        "phone": current_phone,
        "branch": "IT",
        "section": "A",
        "location_lat": student_lat,
        "location_lon": student_lon,
    }
    files = {"selfie": ("selfie.jpg", get_test_selfie(), "image/jpeg")}
    response = httpx.post(API_URL, data=data, files=files, timeout=20.0)
    assert response.status_code == 200, f"Expected Marked, got {response.status_code}: {response.text}"



