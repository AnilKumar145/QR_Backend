import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the database URL
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

print("Verifying database tables...")

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    # Check institutions table
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'institutions'
        )
    """)
    if cursor.fetchone()[0]:
        print("✅ institutions table exists")
    else:
        print("❌ institutions table does not exist")
    
    # Check venues table
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'venues'
        )
    """)
    if cursor.fetchone()[0]:
        print("✅ venues table exists")
    else:
        print("❌ venues table does not exist")
    
    # Check qr_sessions table and venue_id column
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'qr_sessions' AND column_name = 'venue_id'
        )
    """)
    if cursor.fetchone()[0]:
        print("✅ venue_id column exists in qr_sessions table")
    else:
        print("❌ venue_id column does not exist in qr_sessions table")
    
    # Check foreign key constraint
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'qr_sessions'
                AND ccu.table_name = 'venues'
                AND ccu.column_name = 'id'
        )
    """)
    if cursor.fetchone()[0]:
        print("✅ Foreign key constraint exists between qr_sessions.venue_id and venues.id")
    else:
        print("❌ Foreign key constraint does not exist")
    
    # Show all columns in qr_sessions table
    print("\nColumns in qr_sessions table:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'qr_sessions'
        ORDER BY ordinal_position
    """)
    for column in cursor.fetchall():
        print(f"  - {column[0]}: {column[1]} (nullable: {column[2]})")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error verifying tables: {e}")
    sys.exit(1)