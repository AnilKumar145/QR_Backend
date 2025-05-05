import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Get admin token (you'll need to set this or get it from a login)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

if not ADMIN_TOKEN:
    print("Warning: ADMIN_TOKEN not set. You may need to login first.")
    # You could add code here to login and get a token

print("Testing admin statistics endpoints...")

# Test daily statistics endpoint
def test_daily_statistics():
    print("\nTesting daily statistics endpoint...")
    
    # Test with different day ranges
    for days in [1, 7, 30]:
        url = f"{API_BASE_URL}/api/v1/admin/statistics/daily?days={days}"
        print(f"Testing URL: {url}")
        
        try:
            response = requests.get(
                url, 
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
            )
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Endpoint returned {len(data)} days of statistics")
                print(f"Sample data: {json.dumps(dict(list(data.items())[:2]), indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error testing daily statistics: {e}")

# Test summary statistics endpoint
def test_summary_statistics():
    print("\nTesting summary statistics endpoint...")
    
    url = f"{API_BASE_URL}/api/v1/admin/statistics/summary"
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(
            url, 
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Endpoint returned summary statistics")
            print(f"Data: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing summary statistics: {e}")

# Run the tests
if __name__ == "__main__":
    test_daily_statistics()
    test_summary_statistics()
    
    print("\nDone!")