from datetime import datetime

from pydantic import BaseModel


class CourseCreate(BaseModel):
    code: str
    name: str
    description: str = ""
    course_type: str = "academic"


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    course_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class CourseEnrollmentOut(BaseModel):
    id: int
    course_id: int
    user_id: int
    enrolled_at: datetime

    class Config:
        from_attributes = True

