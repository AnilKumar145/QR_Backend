from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Import models to ensure they're registered with SQLAlchemy
from app.models.qr_session import QRSession
from app.models.attendance import Attendance
from app.models.flagged_log import FlaggedLog
from app.models import Base

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
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=600,
    # Add SSL requirement for Render's PostgreSQL
    connect_args={"sslmode": "require"} if is_render or "dpg-" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Move table creation to a separate function
def init_db():
    try:
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
