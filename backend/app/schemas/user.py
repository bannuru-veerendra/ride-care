import uuid

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Request body for POST /auth/register"""
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    """Request body for POST /auth/login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user fields returned by the API (no password)"""
    id: uuid.UUID
    email: EmailStr
    full_name: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response body for POST /auth/login"""
    access_token: str
    token_type: str = "bearer"
