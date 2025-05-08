#!/usr/bin/env python
"""
Verify Migrations Script
This script verifies that migrations were applied correctly.
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

print("Verifying migrations in production...")

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    cursor = conn.cursor()
    
    # Check alembic_version
    cursor.execute("SELECT version_num FROM alembic_version")
    versions = cursor.fetchall()
    print(f"\nCurrent alembic version: {versions}")
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name NOT IN ('pg_stat_statements', 'pg_stat_statements_info', 'alembic_version')
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nFound {len(tables)} tables in production database:")
    for table in tables:
        print(f"  - {table}")
    
    # Check for institutions and venues tables
    if 'institutions' in tables and 'venues' in tables:
        print("\n✓ institutions and venues tables exist")
        
        # Check venue_id in qr_sessions
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'qr_sessions' AND column_name = 'venue_id'
        """)
        
        if cursor.fetchone():
            print("✓ venue_id column exists in qr_sessions table")
            
            # Check foreign key constraint
            cursor.execute("""
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = 'qr_sessions'
                  AND kcu.column_name = 'venue_id'
            """)
            
            if cursor.fetchone():
                print("✓ Foreign key constraint exists for venue_id in qr_sessions")
            else:
                print("✗ Foreign key constraint missing for venue_id in qr_sessions")
        else:
            print("✗ venue_id column does not exist in qr_sessions table")
            
        # Check structure of institutions table
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'institutions'
            ORDER BY ordinal_position
        """)
        
        print("\nStructure of institutions table:")
        for column, data_type in cursor.fetchall():
            print(f"  - {column} ({data_type})")
            
        # Check structure of venues table
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'venues'
            ORDER BY ordinal_position
        """)
        
        print("\nStructure of venues table:")
        for column, data_type in cursor.fetchall():
            print(f"  - {column} ({data_type})")
    else:
        print("\n✗ institutions and/or venues tables do not exist")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)

print("\nMigration verification complete")