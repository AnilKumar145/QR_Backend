import os
import sys
import requests
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Get the database URL
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

# Get the API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

print("Testing selfie retrieval...")

# Connect to the database to get a sample roll number
try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    # Get a sample roll number with a selfie
    cursor.execute("""
        SELECT roll_no, selfie_path 
        FROM attendances 
        WHERE selfie_path IS NOT NULL 
        ORDER BY timestamp DESC 
        LIMIT 1
    """)
    result = cursor.fetchone()
    
    if result:
        roll_no, selfie_path = result
        print(f"Found sample roll number: {roll_no}")
        print(f"Selfie path: {selfie_path}")
        
        # Test the endpoint
        url = f"{API_BASE_URL}/api/v1/utils/selfie/{roll_no}"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, allow_redirects=False)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! Endpoint returned the selfie directly.")
        elif response.status_code == 307:
            redirect_url = response.headers.get('Location')
            print(f"Success! Endpoint redirected to: {redirect_url}")
        else:
            print(f"Error: {response.text}")
    else:
        print("No attendance records with selfies found.")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error testing selfie retrieval: {e}")
    sys.exit(1)

print("\nDone!")