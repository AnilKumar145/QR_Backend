import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection string from environment
database_url = os.getenv("DATABASE_URL")

try:
    # Connect to the database
    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cursor = conn.cursor()
    
    # Check if the column exists
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'flagged_logs' AND column_name = 'details'
    """)
    column_exists = cursor.fetchone() is not None
    
    if not column_exists:
        print("Adding details column to flagged_logs table...")
        
        # Add the column
        cursor.execute("""
            ALTER TABLE flagged_logs 
            ADD COLUMN details TEXT
        """)
        
        # Commit the transaction
        conn.commit()
        print("details column added successfully!")
    else:
        print("details column already exists in flagged_logs table.")
        conn.rollback()
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
    if 'conn' in locals() and conn:
        conn.rollback()
        conn.close()