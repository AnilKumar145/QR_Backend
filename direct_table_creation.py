import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

print("Creating database tables directly...")

# SQL statements to create tables
create_qr_sessions_table = """
CREATE TABLE IF NOT EXISTS qr_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR NOT NULL UNIQUE,
    course_code VARCHAR NOT NULL,
    course_name VARCHAR NOT NULL,
    instructor_name VARCHAR NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

create_attendances_table = """
CREATE TABLE IF NOT EXISTS attendances (
    id SERIAL PRIMARY KEY,
    qr_session_id INTEGER NOT NULL,
    student_id VARCHAR NOT NULL,
    student_name VARCHAR NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qr_session_id) REFERENCES qr_sessions(id)
);
"""

create_institutions_table = """
CREATE TABLE IF NOT EXISTS institutions (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    UNIQUE(name)
);
"""

create_venues_table = """
CREATE TABLE IF NOT EXISTS venues (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    radius_meters FLOAT NOT NULL,
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
"""

add_venue_id_to_qr_sessions = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'qr_sessions' AND column_name = 'venue_id'
    ) THEN
        ALTER TABLE qr_sessions ADD COLUMN venue_id INTEGER;
        ALTER TABLE qr_sessions ADD CONSTRAINT fk_qr_sessions_venue_id 
            FOREIGN KEY (venue_id) REFERENCES venues(id);
    END IF;
END $$;
"""

# Connect to the database and execute the SQL
try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create tables
    print("Creating qr_sessions table...")
    cursor.execute(create_qr_sessions_table)
    
    print("Creating attendances table...")
    cursor.execute(create_attendances_table)
    
    print("Creating institutions table...")
    cursor.execute(create_institutions_table)
    
    print("Creating venues table...")
    cursor.execute(create_venues_table)
    
    print("Adding venue_id to qr_sessions table...")
    cursor.execute(add_venue_id_to_qr_sessions)
    
    # Create or update alembic_version table
    print("Setting up alembic_version table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL, 
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
    """)
    cursor.execute("DELETE FROM alembic_version")
    cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('add_institutions_venues')")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    print("\nTables created successfully!")
    
except Exception as e:
    print(f"Error creating tables: {e}")
    sys.exit(1)