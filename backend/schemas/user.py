from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class Theme(str, Enum):
    light = "light"
    dark = "dark"


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserResponse(BaseModel):
    email: str
    name: str
    profileImage: Optional[str]
    description: Optional[str]
    theme: Theme


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[Theme] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str