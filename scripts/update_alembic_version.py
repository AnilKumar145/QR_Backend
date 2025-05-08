#!/usr/bin/env python
"""
Update Alembic Version Script
This script updates the alembic_version table in production.
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

print("Updating alembic_version in production...")

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Update alembic_version
    cursor.execute("DELETE FROM alembic_version")
    cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('initial_schema')")
    
    print("Successfully updated alembic_version to 'initial_schema'")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error updating alembic_version: {e}")
    sys.exit(1)

print("\nAlembic version updated")
print("Now you can create new migrations from this clean state.")
