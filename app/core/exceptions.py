from fastapi import HTTPException, status
from typing import Dict, Any, Optional

class AttendanceException(HTTPException):
    def __init__(self, detail: str, code: str = "attendance_error"):
        self.error_code = code
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": code,
                "message": detail
            }
        )

class InvalidSessionException(AttendanceException):
    def __init__(self, message: str = "Invalid or expired session"):
        super().__init__(detail=message, code="invalid_session")

class SessionExpiredException(AttendanceException):
    def __init__(self, expires_at: str):
        super().__init__(
            detail=f"Session has expired at {expires_at}",
            code="session_expired"
        )

class SessionNotFoundException(AttendanceException):
    def __init__(self, session_id: str):
        super().__init__(
            detail=f"Session with ID {session_id} not found",
            code="session_not_found"
        )

class DuplicateAttendanceException(AttendanceException):
    def __init__(self, roll_no: str, session_id: str, timestamp: str):
        super().__init__(
            detail=f"Attendance for roll number {roll_no} already marked at {timestamp}",
            code="duplicate_attendance"
        )

class InvalidLocationException(Exception):
    def __init__(
        self, 
        distance: float, 
        lat: float, 
        lon: float, 
        venue_lat: float = None,
        venue_lon: float = None,
        venue_name: str = None,
        max_distance: float = None,
        message: str = None
    ):
        self.distance = distance
        self.lat = lat
        self.lon = lon
        self.venue_lat = venue_lat
        self.venue_lon = venue_lon
        self.venue_name = venue_name
        self.max_distance = max_distance
        
        if not message:
            venue_text = f"from {venue_name}" if venue_name else "from institution"
            message = f"Invalid location. You are {distance:.0f} meters {venue_text}. Maximum allowed distance is {max_distance:.0f} meters."
        
        self.message = message
        super().__init__(self.message)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a structured dictionary for API responses"""
        return {
            "error": "location_out_of_range",
            "message": self.message,
            "details": {
                "your_location": {
                    "lat": self.lat,
                    "lon": self.lon
                },
                "venue_location": {
                    "lat": self.venue_lat,
                    "lon": self.venue_lon,
                    "name": self.venue_name
                } if self.venue_lat and self.venue_lon else None,
                "distance": round(self.distance),
                "max_allowed_distance": round(self.max_distance) if self.max_distance else None
            }
        }

class InvalidCoordinateException(AttendanceException):
    def __init__(self, lat: Optional[float] = None, lon: Optional[float] = None, message: Optional[str] = None):
        if not message:
            if lat is not None and (lat < -90 or lat > 90):
                message = f"Invalid latitude {lat}. Must be between -90 and 90 degrees."
            elif lon is not None and (lon < -180 or lon > 180):
                message = f"Invalid longitude {lon}. Must be between -180 and 180 degrees."
            else:
                message = "Invalid coordinates provided."
        
        super().__init__(detail=message, code="invalid_coordinates")

class CoordinatePrecisionException(AttendanceException):
    def __init__(self, lat_decimals: int = None, lon_decimals: int = None):
        message = f"Coordinates must not exceed 7 decimal places. Got lat:{lat_decimals}, lon:{lon_decimals} decimals."
        super().__init__(detail=message, code="coordinate_precision_error")

class InvalidFileException(AttendanceException):
    def __init__(self, message: str = "Invalid file format or size"):
        super().__init__(detail=message, code="invalid_file")

class FileSizeTooLargeException(InvalidFileException):
    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"File size ({size/1024/1024:.1f}MB) exceeds maximum allowed size ({max_size/1024/1024:.1f}MB)"
        )

class FileTypeNotAllowedException(InvalidFileException):
    def __init__(self, content_type: str, allowed_types: list):
        super().__init__(
            message=f"File type '{content_type}' not allowed. Allowed types: {', '.join(allowed_types)}"
        )




