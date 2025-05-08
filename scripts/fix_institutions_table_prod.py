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

print("Fixing institutions table in PRODUCTION...")
print("WARNING: This will modify the production database!")

# Ask for confirmation before proceeding
confirm = input("\nAre you sure you want to proceed with modifying the production database? (y/n): ")
if confirm.lower() != 'y':
    print("Operation cancelled.")
    sys.exit(0)

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = False  # Use transaction for safety
    cursor = conn.cursor()
    
    # Check if institutions table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'institutions'
        )
    """)
    table_exists = cursor.fetchone()[0]
    
    if not table_exists:
        print("Creating institutions table...")
        cursor.execute("""
            CREATE TABLE institutions (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                city VARCHAR NOT NULL
            )
        """)
        print("✅ institutions table created")
    else:
        print("institutions table already exists, checking columns...")
        
        # Get current columns
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'institutions'
            ORDER BY ordinal_position
        """)
        
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"Current columns: {columns}")
        
        # Check for required columns
        required_columns = {
            'id': 'integer',
            'name': 'character varying',
            'city': 'character varying'
        }
        
        # Remove unwanted columns
        for col in list(columns.keys()):
            if col not in required_columns and col != 'id':
                print(f"Removing column: {col}")
                cursor.execute(f"ALTER TABLE institutions DROP COLUMN IF EXISTS {col}")
        
        # Add missing columns
        for col, data_type in required_columns.items():
            if col not in columns and col != 'id':  # Skip id as it's the primary key
                print(f"Adding column: {col}")
                cursor.execute(f"ALTER TABLE institutions ADD COLUMN {col} {data_type} NOT NULL DEFAULT ''")
        
        # If city column exists but is nullable, make it NOT NULL
        if 'city' in columns:
            cursor.execute("""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'institutions' AND column_name = 'city'
            """)
            is_nullable = cursor.fetchone()[0]
            
            if is_nullable == 'YES':
                print("Making city column NOT NULL...")
                cursor.execute("UPDATE institutions SET city = '' WHERE city IS NULL")
                cursor.execute("ALTER TABLE institutions ALTER COLUMN city SET NOT NULL")
    
    # Verify the table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'institutions'
        ORDER BY ordinal_position
    """)
    
    print("\nFinal institutions table structure:")
    for col_name, data_type, is_nullable in cursor.fetchall():
        print(f"  - {col_name}: {data_type} (nullable: {is_nullable})")
    
    # Commit the transaction
    conn.commit()
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
    print("\nProduction database updated successfully!")
    
except Exception as e:
    # Rollback in case of error
    if conn:
        conn.rollback()
    print(f"Error updating production database: {e}")
    sys.exit(1)