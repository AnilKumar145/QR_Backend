import os
import sys
import psycopg2
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to: {PROD_DB_URL}")

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = False
    cursor = conn.cursor()
    
    # Create a small test image (1x1 pixel PNG)
    test_image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    
    # Find a test record to update
    cursor.execute("SELECT id FROM attendances LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        test_id = result[0]
        print(f"Found test record with ID: {test_id}")
        
        # Update the record with test data
        cursor.execute(
            "UPDATE attendances SET selfie_data = %s, selfie_content_type = %s WHERE id = %s",
            (test_image, "image/png", test_id)
        )
        
        conn.commit()
        print(f"Updated record {test_id} with test image data")
        
        # Verify the data was stored correctly
        cursor.execute(
            "SELECT selfie_data, selfie_content_type FROM attendances WHERE id = %s",
            (test_id,)
        )
        
        result = cursor.fetchone()
        if result and result[0]:
            image_data = result[0]
            content_type = result[1]
            print(f"Retrieved image data: {len(image_data)} bytes")
            print(f"Content type: {content_type}")
            print("Test successful! The columns are working correctly.")
        else:
            print("Failed to retrieve test data")
    else:
        print("No attendance records found to test with")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
