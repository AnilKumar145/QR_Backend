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

print("Creating tables directly...")

# SQL statements to create the tables
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
    -- Check if venue_id column exists in qr_sessions
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'qr_sessions' AND column_name = 'venue_id'
    ) THEN
        -- Add venue_id column to qr_sessions
        ALTER TABLE qr_sessions ADD COLUMN venue_id INTEGER;
        
        -- Add foreign key constraint
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

# Connect to the database and execute the SQL
try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create institutions table
    print("Creating institutions table...")
    cursor.execute(create_institutions_table)
    
    # Create venues table
    print("Creating venues table...")
    cursor.execute(create_venues_table)
    
    # Add venue_id to qr_sessions
    print("Adding venue_id to qr_sessions table...")
    cursor.execute(add_venue_id_to_qr_sessions)
    
    # Update alembic_version table to mark this migration as applied
    print("Updating alembic_version table...")
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')")
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        # Update the version
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('add_institutions_venues')")
        print("Updated alembic_version table to 'add_institutions_venues'")
    else:
        # Create the table
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('add_institutions_venues')")
        print("Created alembic_version table with version 'add_institutions_venues'")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    print("\nTables created successfully!")
    
except Exception as e:
    print(f"Error creating tables: {e}")
    sys.exit(1)