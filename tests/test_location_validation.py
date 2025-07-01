import pytest
import httpx
from datetime import datetime, timedelta
import itertools
import time
import random

# Adjust these as needed for your local or deployed API
API_URL = "http://127.0.0.1:8000/api/v1/attendance/mark"

# Example test data (replace with your real session_id, venue, etc.)
TEST_CASES = [
    # Format: (venue_city, institution, venue_name, venue_lat, venue_lon, student_city, student_lat, student_lon, test_type, expected_outcome)
    ("Hyderabad", "Saracity University", "IT Hall", 17.444, 78.3498, "Mumbai", 19.076, 72.8777, "CrossCity", "Rejected"),
    ("Hyderabad", "Saracity University", "AI Lab", 17.4435, 78.3502, "Bengaluru", 12.9716, 77.5946, "CrossCity", "Rejected"),
    ("Bengaluru", "CodeZone Institute", "ML Lab", 12.9716, 77.5946, "Chennai", 13.0827, 80.2707, "CrossCity", "Rejected"),
    ("Bengaluru", "CodeZone Institute", "Seminar Hall", 12.972, 77.595, "Delhi", 28.6139, 77.209, "CrossCity", "Rejected"),
    ("Mumbai", "Raj University", "Data Hall", 19.076, 72.8777, "Hyderabad", 17.385, 78.4867, "CrossCity", "Rejected"),
    ("Mumbai", "Raj University", "Quantum Lab", 19.0755, 72.8772, "Chennai", 13.0827, 80.2707, "CrossCity", "Rejected"),
    ("Chennai", "Oceanic College", "Robotics Hall", 13.0827, 80.2707, "Bengaluru", 12.9716, 77.5946, "CrossCity", "Rejected"),
    ("Chennai", "Oceanic College", "IoT Lab", 13.083, 80.2709, "Delhi", 28.6139, 77.209, "CrossCity", "Rejected"),
    ("Delhi", "MetroTech University", "Smart Hall", 28.6139, 77.209, "Mumbai", 19.076, 72.8777, "CrossCity", "Rejected"),
    ("Delhi", "MetroTech University", "Dev Arena", 28.6142, 77.2095, "Hyderabad", 17.385, 78.4867, "CrossCity", "Rejected"),
]

SESSION_IDS = {
    "IT Hall": "8c728e8f-545d-45d4-a241-a5c56a92c3a0",
    "AI Lab": "a8690d0e-6b36-444c-bad5-b65982ce9b65",
    "ML Lab": "350cb6e8-962d-45a3-8f83-7f867625a814",
    "Seminar Hall": "9c1d8390-258b-4f46-9b1d-44075eef23dc",
    "Data Hall": "8f0e5fc2-d123-4e8a-b90a-ac6a80615b81",
    "Quantum Lab": "6fd8da11-ff29-44a3-916c-21d4db8f787e",
    "Robotics Hall": "b2e307ae-006d-44e1-bed7-7ded31bc4779",
    "IoT Lab": "e0605ade-dc0d-4c4a-9ec8-34719c4c44a1",
    "Smart Hall": "8887f599-195c-4def-8aab-f844e3754b59",
    "Dev Arena": "edf73ff1-8096-4fa2-9560-7ea8bfd70909",
}

roll_no_counter = itertools.count(start=1200)
phone_counter = itertools.count(start=9000000000)
branches = ["IT", "CSE", "MECH", "AI", "ECE", "CIVIL"]
sections = ["A", "B", "C", "D", "E"]
branch_cycle = itertools.cycle(branches)
section_cycle = itertools.cycle(sections)

def get_test_selfie():
    # Return a small valid JPEG file as bytes (replace with a real file in practice)
    return b"\xff\xd8\xff\xe0" + b"0" * 1000 + b"\xff\xd9"

@pytest.mark.parametrize(
    "venue_city, institution, venue, venue_lat, venue_lon, student_city, student_lat, student_lon, test_type, expected_outcome",
    TEST_CASES
)
def test_location_validation(venue_city, institution, venue, venue_lat, venue_lon, student_city, student_lat, student_lon, test_type, expected_outcome):
    session_id = SESSION_IDS[venue]
    # Use a unique, sequential roll number like 208W1A12001, 208W1A12002, ...
    current_roll_no = f"208W1A12{next(roll_no_counter):03d}"
    current_phone = str(next(phone_counter))
    current_branch = next(branch_cycle)
    current_section = next(section_cycle)
    data = {
        "session_id": session_id,
        "name": f"Test Student {venue_city}",
        "email": f"test_{current_roll_no}@example.com",
        "roll_no": current_roll_no,
        "phone": current_phone,
        "branch": current_branch,
        "section": current_section,
        "location_lat": student_lat,
        "location_lon": student_lon,
    }
    files = {"selfie": ("selfie.jpg", get_test_selfie(), "image/jpeg")}
    response = httpx.post(API_URL, data=data, files=files)
    if expected_outcome == "Marked":
        assert response.status_code == 200, f"Expected Marked, got {response.status_code}: {response.text}"
    else:
        assert response.status_code != 200, f"Expected Rejected, got {response.status_code}: {response.text}" 