import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to: {PROD_DB_URL}")

# Create engine with production database
engine = create_engine(PROD_DB_URL)

# Connect and check schema information
try:
    with engine.connect() as connection:
        # Check current schema
        result = connection.execute(text("SELECT current_schema()"))
        current_schema = result.scalar()
        print(f"Current schema: {current_schema}")
        
        # Check search path
        result = connection.execute(text("SHOW search_path"))
        search_path = result.scalar()
        print(f"Search path: {search_path}")
        
        # List all schemas
        result = connection.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            ORDER BY schema_name
        """))
        schemas = [row[0] for row in result]
        print(f"Available schemas: {schemas}")
        
        # List tables in the current schema
        result = connection.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = current_schema()
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"Tables in current schema: {tables}")
        
        # Check if attendances table exists in any schema
        result = connection.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name = 'attendances'
            ORDER BY table_schema
        """))
        attendances_tables = [(row[0], row[1]) for row in result]
        print(f"Attendances tables in all schemas: {attendances_tables}")
        
        # Check alembic version table
        result = connection.execute(text("""
            SELECT version_num
            FROM alembic_version
            ORDER BY version_num
        """))
        versions = [row[0] for row in result]
        print(f"Alembic versions: {versions}")
        
except Exception as e:
    print(f"Error connecting to database: {e}")