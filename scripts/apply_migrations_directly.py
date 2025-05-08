#!/usr/bin/env python
"""
Apply Migrations Directly Script
This script applies migrations directly to the production database without using Alembic.
"""

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

print("Applying migrations directly to production...")

# SQL statements to create institutions and venues tables
create_institutions_table = """
CREATE TABLE IF NOT EXISTS institutions (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    address VARCHAR,
    latitude FLOAT,
    longitude FLOAT
);
"""

create_venues_table = """
CREATE TABLE IF NOT EXISTS venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    institution_id INTEGER NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    geofence_radius FLOAT,
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);
"""

# SQL statement to add venue_id to qr_sessions
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

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if tables already exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('institutions', 'venues')
    """)
    
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    # Create institutions table if it doesn't exist
    if 'institutions' not in existing_tables:
        print("Creating institutions table...")
        cursor.execute(create_institutions_table)
        print("institutions table created successfully")
    else:
        print("institutions table already exists")
    
    # Create venues table if it doesn't exist
    if 'venues' not in existing_tables:
        print("Creating venues table...")
        cursor.execute(create_venues_table)
        print("venues table created successfully")
    else:
        print("venues table already exists")
    
    # Add venue_id to qr_sessions
    print("Adding venue_id to qr_sessions table (if it doesn't exist)...")
    cursor.execute(add_venue_id_to_qr_sessions)
    print("venue_id column added to qr_sessions (or already exists)")
    
    # Check if venue_id column exists in qr_sessions
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'qr_sessions' AND column_name = 'venue_id'
        )
    """)
    venue_id_exists = cursor.fetchone()[0]
    
    if venue_id_exists:
        print("Confirmed: venue_id column exists in qr_sessions table")
    else:
        print("Warning: venue_id column does not exist in qr_sessions table")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error applying migrations: {e}")
    sys.exit(1)

print("\nMigrations applied successfully!")
print("Run 'python scripts/verify_migrations.py' to verify the changes")