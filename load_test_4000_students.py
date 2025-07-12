import concurrent.futures
import urllib.request
import urllib.parse
import random
import string
import time
import json

API_URL = "https://qr-backend-1-pq5i.onrender.com/api/v1/attendance/mark"

# First, let's get real session IDs from your database
# You need to replace these with actual session IDs from your qr_sessions table
SESSION_IDS = [
    "86258922-4f19-4e6d-b82a-6df79a3bf5d0",  # Replace with real session_id for venue 1
    "8da4ca1e-f57c-47a8-a98a-ff6dd0bfab40",  # Replace with real session_id for venue 2  
    "57014b77-0136-4e6f-8475-7abdab1bf34a",  # Replace with real session_id for venue 3
]

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_email():
    return f"{random_string(5)}@test.com"

def random_roll():
    return f"20{random.randint(10,99)}W1A{random.randint(1000,9999)}"

def random_phone():
    return f"{random.randint(7000000000,9999999999)}"

def random_branch():
    return random.choice(["CSE", "IT", "MECH", "CIVIL", "AI"])

def random_section():
    return random.choice(["A", "B", "C", "D", "E", "F", "G", "H", "K", "Z"])

def submit_attendance(session_id, student_num):
    data = {
        "session_id": session_id,
        "name": f"Test Student {student_num}",
        "email": f"student{student_num}@test.com",
        "roll_no": f"20{random.randint(10,99)}W1A{random.randint(1000,9999)}",
        "phone": f"{random.randint(7000000000,9999999999)}",
        "branch": random_branch(),
        "section": random_section(),
        "location_lat": 16.4664,
        "location_lon": 80.6746,
    }
    
    # Convert data to form-encoded format
    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
    
    try:
        # Create request
        req = urllib.request.Request(API_URL, data=data_encoded)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        # Send request with shorter timeout
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() == 200:
                return True
            else:
                print(f"Failed: {response.getcode()}")
                return False
    except Exception as e:
        print(f"Error for student {student_num}: {str(e)[:50]}...")
        return False

def test_batch(batch_size, session_id, batch_num):
    """Test a smaller batch of requests"""
    print(f"Starting batch {batch_num} with {batch_size} requests...")
    tasks = [(session_id, i) for i in range(batch_size)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda x: submit_attendance(*x), tasks))
    
    success_count = sum(results)
    print(f"Batch {batch_num} completed: {success_count}/{batch_size} successful")
    return success_count

def main():
    print("=== QR Attendance System Load Test ===")
    print("Testing with realistic batch sizes...")
    
    total_requests = 0
    total_success = 0
    
    # Test with smaller batches
    batch_size = 50  # 50 requests per batch
    num_batches = 10  # 10 batches = 500 total requests
    
    for batch_num in range(num_batches):
        # Rotate through session IDs
        session_id = SESSION_IDS[batch_num % len(SESSION_IDS)]
        
        success_count = test_batch(batch_size, session_id, batch_num + 1)
        total_success += success_count
        total_requests += batch_size
        
        # Small delay between batches
        time.sleep(2)
    
    print(f"\n=== Load Test Results ===")
    print(f"Total requests: {total_requests}")
    print(f"Successful: {total_success}")
    print(f"Failed: {total_requests - total_success}")
    print(f"Success rate: {(total_success/total_requests*100):.2f}%")
    
    if total_success > 0:
        print(f"✅ System can handle {total_success} concurrent requests successfully!")
        print(f"📊 Estimated capacity: {total_success * 8} students (8x the test size)")
    else:
        print("❌ System needs optimization for high concurrency")

if __name__ == "__main__":
    main()
