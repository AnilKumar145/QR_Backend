import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("DATABASE_URL environment variable not set")
    sys.exit(1)

# Create engine
engine = create_engine(database_url)

# SQL to check if admin_users table exists and add is_active column if needed
sql = """
DO $$
BEGIN
    -- Check if admin_users table exists
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'admin_users'
    ) THEN
        -- Check if is_active column exists
        IF NOT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'admin_users' 
            AND column_name = 'is_active'
        ) THEN
            -- Add is_active column
            ALTER TABLE admin_users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
            RAISE NOTICE 'Added is_active column to admin_users table';
        ELSE
            RAISE NOTICE 'is_active column already exists in admin_users table';
        END IF;
    ELSE
        RAISE NOTICE 'admin_users table does not exist';
    END IF;
END
$$;
"""

try:
    # Connect to database and execute SQL
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("Script executed successfully")
except Exception as e:
    print(f"Error: {e}")