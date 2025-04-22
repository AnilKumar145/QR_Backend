import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

def setup_test_database():
    # Load environment variables
    load_dotenv('.env.test')
    
    # Parse DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not found in .env.test")
    
    # Extract connection details
    db_parts = db_url.replace('postgresql://', '').split('@')
    user_pass = db_parts[0].split(':')
    host_db = db_parts[1].split('/')
    
    username = user_pass[0]
    password = user_pass[1]
    host = host_db[0].split(':')[0]
    port = host_db[0].split(':')[1] if ':' in host_db[0] else '5432'
    database = host_db[1]
    
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database='postgres'  # Connect to default database first
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    try:
        # Create test database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f'CREATE DATABASE {database}')
            print(f"Created test database: {database}")
        else:
            print(f"Test database already exists: {database}")
            
    except Exception as e:
        print(f"Error setting up test database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_test_database()
