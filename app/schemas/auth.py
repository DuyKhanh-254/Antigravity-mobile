from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str
    device_name: str


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str
    device_fingerprint: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str
