from datetime import datetime
from typing import Literal

from pydantic import BaseModel


TaskStatusLiteral = Literal["backlog", "todo", "in_progress", "review", "done", "returned"]


class TaskCreate(BaseModel):
    team_id: int
    creator_name: str
    creator_handle: str | None = None
    name: str
    description: str = ""
    attachment_url: str = ""
    file_rules: str = ""
    category: str = "general"
    deadline: datetime | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    assignee_id: int | None = None
    name: str | None = None
    description: str | None = None
    attachment_url: str | None = None
    file_rules: str | None = None
    category: str | None = None
    deadline: datetime | None = None
    status: TaskStatusLiteral | None = None
    grade: int | None = None
    rejection_flag: bool | None = None
    rejection_reason: str | None = None


class TaskOut(BaseModel):
    id: int
    team_id: int
    assignee_id: int | None = None
    creator_name: str
    name: str
    description: str
    attachment_url: str
    file_rules: str
    category: str
    deadline: datetime | None = None
    status: TaskStatusLiteral
    grade: int | None = None
    closed: bool = False
    rejection_flag: bool
    rejection_reason: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubTaskCreate(BaseModel):
    task_id: int
    title: str


class SubTaskUpdate(BaseModel):
    is_done: bool


class SubTaskOut(BaseModel):
    id: int
    task_id: int
    title: str
    is_done: bool

    class Config:
        from_attributes = True


class TaskPermissionCreate(BaseModel):
    task_id: int
    role_name: str
    can_access: bool = True
    can_grade: bool = False
    can_return: bool = False


class TaskPermissionOut(BaseModel):
    id: int
    task_id: int
    role_name: str
    can_access: bool
    can_grade: bool
    can_return: bool

    class Config:
        from_attributes = True


class TaskLogOut(BaseModel):
    id: int
    task_id: int
    action: str
    actor: str
    details: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskSubmissionOut(BaseModel):
    id: int
    task_id: int
    submitter_handle: str
    title: str
    description: str
    original_filename: str | None = None
    file_url: str | None = None
    file_size: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True