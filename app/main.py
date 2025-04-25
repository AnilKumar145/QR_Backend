from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.api.api import api_router
from app.core.middleware import RateLimitMiddleware
from app.db.base import init_db

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

# Initialize database tables
@app.on_event("startup")
async def startup_event():
    init_db()

# Add Rate Limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_limit=100,
    window_seconds=60
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://qr-frontend-attendancesystem.vercel.app",
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
