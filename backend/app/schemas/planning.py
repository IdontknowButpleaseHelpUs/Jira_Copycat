from datetime import datetime

from pydantic import BaseModel


class PlanningCreate(BaseModel):
    team_id: int
    title: str
    timeline_start: datetime
    timeline_end: datetime
    category: str = "general"


class PlanningOut(BaseModel):
    id: int
    team_id: int
    title: str
    timeline_start: datetime
    timeline_end: datetime
    category: str

    class Config:
        from_attributes = True