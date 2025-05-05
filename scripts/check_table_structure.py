import os
import sys
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def check_table_structure():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return
    
    # Create engine
    engine = create_engine(database_url)
    
    # Connect and check table structure
    with engine.connect() as connection:
        # Get table information
        inspector = inspect(engine)
        
        # Check if table exists
        if 'attendances' not in inspector.get_table_names():
            print("Table 'attendances' does not exist")
            return
        
        # Get column information
        columns = inspector.get_columns('attendances')
        
        print("Columns in 'attendances' table:")
        for column in columns:
            print(f"- {column['name']}: {column['type']} (nullable: {column['nullable']})")
        
        # Check specifically for our new columns
        column_names = [col['name'] for col in columns]
        if 'selfie_data' in column_names:
            print("\nselfie_data column exists ✓")
        else:
            print("\nselfie_data column does NOT exist ✗")
            
        if 'selfie_content_type' in column_names:
            print("selfie_content_type column exists ✓")
        else:
            print("selfie_content_type column does NOT exist ✗")

if __name__ == "__main__":
    check_table_structure()