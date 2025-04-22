from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app: FastAPI, 
        requests_limit: int = 100,  # requests per window
        window_seconds: int = 60     # window size in seconds
    ):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # ip: [timestamp1, timestamp2, ...]

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Remove old requests outside the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time <= self.window_seconds
        ]
        
        # Check if limit is exceeded
        if len(self.requests[client_ip]) >= self.requests_limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response

