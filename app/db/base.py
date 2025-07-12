from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Import Base from base_class instead of defining it here
from app.db.base_class import Base

load_dotenv()

# Get database URL from environment
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Handle special cases for database URL
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Determine if we're running on Render
is_render = os.getenv("RENDER") == "true"

# Create engine with appropriate settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=50,           # Increased from 5 to 50
    max_overflow=100,       # Increased from 10 to 100
    pool_timeout=60,        # Increased from 30 to 60 seconds
    pool_recycle=600,
    pool_pre_ping=True,     # Added connection health check
    # Add SSL requirement for Render's PostgreSQL
    connect_args={"sslmode": "require"} if is_render or "dpg-" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Move table creation to a separate function
def init_db():
    try:
        # Import models here to avoid circular imports
        from app.models.qr_session import QRSession
        from app.models.attendance import Attendance
        from app.models.admin_user import AdminUser  # Changed from Admin to AdminUser
        from app.models.flagged_log import FlaggedLog
        from app.models.venue import Venue
        from app.models.institution import Institution
        
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

def get_db():
    db = SessionLocal()
    try:
        # Test the connection
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        print(f"DATABASE ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

