from fastapi import APIRouter
from app.api.endpoints import attendance, qr_session, utils, admin

api_router = APIRouter()

api_router.include_router(
    qr_session.router,
    prefix="/qr-session",
    tags=["qr-session"]
)

api_router.include_router(
    attendance.router,
    prefix="/attendance",
    tags=["attendance"]
)

api_router.include_router(
    utils.router,
    prefix="/utils",
    tags=["utils"]
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"]
)

