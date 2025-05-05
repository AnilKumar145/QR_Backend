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

# Connect and add columns directly
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
        
        # Check if columns exist in this schema
        result = connection.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema}'
            AND table_name = 'attendances' 
            AND column_name IN ('selfie_data', 'selfie_content_type')
        """))
        
        existing_columns = [row[0] for row in result]
        print(f"Existing columns: {existing_columns}")
        
        # Begin transaction
        trans = connection.begin()
        
        try:
            # Add selfie_data column if it doesn't exist
            if 'selfie_data' not in existing_columns:
                print("Adding selfie_data column...")
                connection.execute(text(f"""
                    ALTER TABLE {schema}.attendances 
                    ADD COLUMN selfie_data BYTEA
                """))
            
            # Add selfie_content_type column if it doesn't exist
            if 'selfie_content_type' not in existing_columns:
                print("Adding selfie_content_type column...")
                connection.execute(text(f"""
                    ALTER TABLE {schema}.attendances 
                    ADD COLUMN selfie_content_type VARCHAR
                """))
            
            # Commit transaction
            trans.commit()
            print("Columns added successfully!")
            
        except Exception as e:
            # Rollback transaction on error
            trans.rollback()
            print(f"Error adding columns: {e}")
            raise
        
        # Verify columns were added
        result = connection.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema}'
            AND table_name = 'attendances' 
            AND column_name IN ('selfie_data', 'selfie_content_type')
        """))
        
        updated_columns = [row[0] for row in result]
        print(f"Updated columns: {updated_columns}")
        
except Exception as e:
    print(f"Error connecting to database: {e}")