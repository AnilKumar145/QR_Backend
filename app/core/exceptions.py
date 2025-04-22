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

class InvalidLocationException(AttendanceException):
    def __init__(self, distance: float):
        super().__init__(
            detail=f"Invalid location. Distance from institution: {distance:.2f} km"
        )

class InvalidFileException(AttendanceException):
    def __init__(self):
        super().__init__(
            detail="Invalid file format or size"
        )