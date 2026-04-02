from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    description: str = ""
    join_code: str


class TeamOut(BaseModel):
    id: int
    name: str
    description: str
    join_code: str

    class Config:
        from_attributes = True


class TeamMemberCreate(BaseModel):
    team_id: int
    display_name: str
    handle: str
    role_name: str = "member"


class TeamMemberJoin(BaseModel):
    display_name: str
    handle: str
    role_name: str = "member"


class TeamMemberOut(BaseModel):
    id: int
    team_id: int
    display_name: str
    handle: str
    role_name: str
    is_active: bool

    class Config:
        from_attributes = True