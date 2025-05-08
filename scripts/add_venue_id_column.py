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

print("Adding venue_id column to qr_sessions table...")

# SQL to add the venue_id column
add_venue_id_sql = """
-- First check if the column exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'qr_sessions' AND column_name = 'venue_id'
    ) THEN
        -- Add the column
        ALTER TABLE qr_sessions ADD COLUMN venue_id INTEGER;
        
        -- Add the foreign key constraint
        ALTER TABLE qr_sessions 
        ADD CONSTRAINT fk_qr_sessions_venue_id 
        FOREIGN KEY (venue_id) REFERENCES venues(id);
        
        RAISE NOTICE 'Added venue_id column to qr_sessions table';
    ELSE
        RAISE NOTICE 'venue_id column already exists in qr_sessions table';
    END IF;
END
$$;
"""

try:
    # Connect to the database
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Execute the SQL
    cursor.execute(add_venue_id_sql)
    
    # Verify the column was added
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
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    print("Done!")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)