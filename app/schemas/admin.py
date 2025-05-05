from pydantic import BaseModel

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AdminCreateRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    # email field removed
