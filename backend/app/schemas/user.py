from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class Theme(str, Enum):
    light = "light"
    dark = "dark"


class RegisterRequest(BaseModel):
    handle: str
    name: str
    email: Optional[EmailStr] = None
    password: str


class LoginRequest(BaseModel):
    handle: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    handle: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    handle: str
    handle_changes_left: int
    name: str
    email: Optional[str] = None
    profile_image: Optional[str] = None
    description: Optional[str] = None
    theme: Theme

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    theme: Optional[Theme] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str