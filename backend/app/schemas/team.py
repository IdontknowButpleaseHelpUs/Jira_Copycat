from datetime import datetime

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    name: str
    description: str = ""
    join_code: str
    creator_handle: str | None = None
    creator_display_name: str | None = None


class TeamOut(BaseModel):
    id: int
    name: str
    description: str
    join_code: str

    class Config:
        from_attributes = True


class InviteMemberRequest(BaseModel):
    team_id: int
    invitee_handle: str = Field(..., min_length=1)
    inviter_handle: str = Field(..., min_length=1)


class JoinTeamRequest(BaseModel):
    handle: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)


class TeamMemberOut(BaseModel):
    id: int
    team_id: int
    display_name: str
    handle: str
    role_name: str
    is_active: bool

    class Config:
        from_attributes = True


class JoinRequestOut(BaseModel):
    id: int
    team_id: int
    handle: str
    display_name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
