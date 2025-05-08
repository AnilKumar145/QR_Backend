#!/usr/bin/env python
"""
Verify Production Schema Script
This script checks if the production database schema matches what we expect.
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

print(f"Connecting to production database...")

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nFound {len(tables)} tables in production database:")
    for table in tables:
        print(f"  - {table}")
    
    # Check for expected tables
    expected_tables = ['qr_sessions', 'attendances', 'institutions', 'venues', 'alembic_version']
    missing_tables = [table for table in expected_tables if table not in tables]
    
    if missing_tables:
        print(f"\n❌ Missing tables: {missing_tables}")
    else:
        print("\n✅ All expected tables exist")
    
    # Check columns for each table
    for table in tables:
        if table in expected_tables:
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print(f"\nColumns in {table} table:")
            for col_name, data_type, is_nullable in columns:
                print(f"  - {col_name}: {data_type} (nullable: {is_nullable})")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)

print("\n✨ Schema verification complete")