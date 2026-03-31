from beanie import Document, Indexed
from pydantic import EmailStr, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class Theme(str, Enum):
    light = "light"
    dark = "dark"


class User(Document):
    email: Indexed(EmailStr, unique=True)
    name: str
    passwordHash: str
    profileImage: Optional[str] = None
    description: Optional[str] = None
    theme: Theme = Theme.light
    refresh_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"