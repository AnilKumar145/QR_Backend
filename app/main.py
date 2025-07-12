from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import os
import logging
import traceback
from sqlalchemy.sql import text

from app.core.config import settings
from app.api.api import api_router
from app.core.middleware import RateLimitMiddleware
from app.db.base import init_db, get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create required directories
os.makedirs(settings.STATIC_FILES_DIR, exist_ok=True)
os.makedirs(settings.SELFIE_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    QR Attendance System API
    """,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/login")


# Initialize database tables
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Starting application...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Add Rate Limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_limit=5000,    # Increased from 100 to 5000 requests per window
    window_seconds=60       # 1 minute window
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://qr-frontend-w1va.vercel.app",  # Old frontend URL
        "https://qr-frontend-om5a.onrender.com",  # New Render frontend URL
        "https://new-attendance-form.vercel.app",  # <--- Add this line
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=settings.STATIC_FILES_DIR), name="static")

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION
    }

@app.get("/health")
def health_check():
    """Health check endpoint to verify the API is running"""
    try:
        # Test database connection
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": settings.VERSION
        }
