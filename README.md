# QR Attendance System Backend
## API Endpoints
### QR Session
- POST `/api/v1/qr-session/generate` - Generate new QR session- POST `/api/v1/qr-session/validate` - Validate QR session
### Attendance
- POST `/api/v1/attendance/mark` - Mark attendance with selfie- GET `/api/v1/attendance/history` - Get attendance history
### Utils
- GET `/api/v1/utils/location/validate` - Validate location
## Setup for Frontend Integration
1. Install dependencies:```bash
pip install -r requirements.txt```
2. Configure environment:
- Copy `.env.example` to `.env`- Update variables as needed
3. Run development server:
```bashuvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
4. API Documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

















