from datetime import datetime

from pydantic import BaseModel


class Message(BaseModel):
    message: str


class BaseOut(BaseModel):
    id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True