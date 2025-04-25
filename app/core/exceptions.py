from fastapi import HTTPException, status

class AttendanceException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class InvalidSessionException(AttendanceException):
    def __init__(self):
        super().__init__(detail="Invalid or expired session")

class InvalidLocationException(Exception):
    def __init__(self, distance: float, lat: float, lon: float, message: str = None):
        self.distance = distance
        self.lat = lat
        self.lon = lon
        self.message = message or f"Invalid location. Distance from institution: {distance:.2f} meters"
        super().__init__(self.message)

class InvalidFileException(AttendanceException):
    def __init__(self):
        super().__init__(
            detail="Invalid file format or size"
        )



