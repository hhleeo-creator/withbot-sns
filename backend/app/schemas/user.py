from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    google_id: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class GoogleLoginRequest(BaseModel):
    google_token: str


class LoginResponse(BaseModel):
    success: bool
    user_id: int
    email: str
    name: str
    session_token: str
    ai_account: Optional[dict] = None
