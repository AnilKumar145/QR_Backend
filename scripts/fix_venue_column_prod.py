import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print("Fixing venue column name in PRODUCTION...")
print("WARNING: This will modify the production database!")

# Ask for confirmation before proceeding
confirm = input("\nAre you sure you want to proceed with modifying the production database? (y/n): ")
if confirm.lower() != 'y':
    print("Operation cancelled.")
    sys.exit(0)

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if geofence_radius exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'venues' AND column_name = 'geofence_radius'
        )
    """)
    geofence_exists = cursor.fetchone()[0]
    
    # Check if radius_meters exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'venues' AND column_name = 'radius_meters'
        )
    """)
    radius_exists = cursor.fetchone()[0]
    
    if geofence_exists and not radius_exists:
        print("Renaming geofence_radius to radius_meters...")
        cursor.execute("ALTER TABLE venues RENAME COLUMN geofence_radius TO radius_meters")
        print("✅ Column renamed successfully")
    elif radius_exists:
        print("✅ radius_meters column already exists")
    else:
        print("❌ Neither geofence_radius nor radius_meters exists")
        print("Adding radius_meters column...")
        cursor.execute("ALTER TABLE venues ADD COLUMN radius_meters FLOAT")
        print("✅ radius_meters column added")
    
    # Verify the column exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'venues' AND column_name = 'radius_meters'
        )
    """)
    if cursor.fetchone()[0]:
        print("✅ radius_meters column exists in venues table")
    else:
        print("❌ radius_meters column does not exist in venues table")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    print("\nProduction database updated successfully!")
    
except Exception as e:
    print(f"Error updating production database: {e}")
    sys.exit(1)