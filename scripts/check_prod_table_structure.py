import os
import sys
from sqlalchemy import create_engine, inspect, text
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

# Connect and check table structure
try:
    with engine.connect() as connection:
        # Find the schema containing the attendances table
        result = connection.execute(text("""
            SELECT table_schema
            FROM information_schema.tables 
            WHERE table_name = 'attendances'
        """))
        
        schemas = [row[0] for row in result]
        
        if not schemas:
            print("Error: 'attendances' table not found in any schema")
            sys.exit(1)
        
        schema = schemas[0]
        print(f"Found 'attendances' table in schema: {schema}")
        
        # Get column information for this schema
        result = connection.execute(text(f"""
            SELECT 
                column_name, 
                data_type, 
                is_nullable
            FROM information_schema.columns 
            WHERE table_schema = '{schema}'
            AND table_name = 'attendances' 
            ORDER BY ordinal_position
        """))
        
        print(f"\nColumns in 'attendances' table (PRODUCTION, schema: {schema}):")
        columns = []
        for row in result:
            column_name = row[0]
            data_type = row[1]
            nullable = row[2]
            print(f"- {column_name}: {data_type} (nullable: {nullable})")
            columns.append(column_name)
        
        # Check specifically for our new columns
        if 'selfie_data' in columns:
            print("\nselfie_data column exists ✓")
        else:
            print("\nselfie_data column does NOT exist ✗")
            
        if 'selfie_content_type' in columns:
            print("selfie_content_type column exists ✓")
        else:
            print("selfie_content_type column does NOT exist ✗")
except Exception as e:
    print(f"Error connecting to database: {e}")
