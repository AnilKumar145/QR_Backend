from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from app.core.config import settings
from app.api.api import api_router
from app.core.middleware import RateLimitMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    QR Attendance System API
    
    Features:
    * QR Code Generation for Attendance Sessions
    * Location-based Attendance Validation
    * Selfie Upload with Attendance
    * Admin Dashboard APIs
    
    For authentication, use the /token endpoint to obtain your access token.
    """,
    contact={
        "name": "Admin",
        "email": "admin@example.com",
    },
    license_info={
        "name": "Private",
    },
)

# Add Rate Limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_limit=100,
    window_seconds=60
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
