# Import Base from base_class to make it available to all models
from app.db.base_class import Base

# Import all models to make them available
from app.models.qr_session import QRSession
from app.models.attendance import Attendance
from app.models.admin_user import AdminUser
from app.models.flagged_log import FlaggedLog

