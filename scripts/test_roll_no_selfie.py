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

# Get the API base URL (update the port if needed)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

print("Testing roll number selfie retrieval...")

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
        LIMIT 5
    """)
    results = cursor.fetchall()
    
    if results:
        for roll_no, selfie_path in results:
            print(f"\nTesting roll number: {roll_no}")
            print(f"Selfie path: {selfie_path}")
            
            # Test the endpoint
            url = f"{API_BASE_URL}/api/v1/utils/selfie/{roll_no}"
            print(f"Testing URL: {url}")
            
            response = requests.get(url, allow_redirects=False)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("Success! Endpoint returned the selfie directly.")
                print(f"Content type: {response.headers.get('Content-Type')}")
                print(f"Content length: {len(response.content)} bytes")
            elif response.status_code == 307:
                redirect_url = response.headers.get('Location')
                print(f"Success! Endpoint redirected to: {redirect_url}")
                
                # Follow the redirect to verify it works
                redirect_response = requests.get(redirect_url)
                print(f"Redirect status code: {redirect_response.status_code}")
                if redirect_response.status_code == 200:
                    print("Successfully retrieved image from redirect URL")
                else:
                    print(f"Failed to retrieve image from redirect URL: {redirect_response.text}")
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
