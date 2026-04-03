from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, Notification, Task, TeamMember
from app.team_access import user_by_handle

router = APIRouter(prefix="/tasks", tags=["comments"])


class CommentCreate(BaseModel):
    author_id: int
    author_role: str = "MEMBER"
    content: str


class CommentOut(BaseModel):
    id: int
    task_id: int
    author_id: int
    author_name: str
    author_role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{task_id}/comments", response_model=list[CommentOut])
def list_comments(task_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at.asc()).all()


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(task_id: int, body: CommentCreate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    member = db.query(TeamMember).filter(TeamMember.id == body.author_id).first()
    author_name = member.display_name if member else f"User #{body.author_id}"

    comment = Comment(
        task_id=task_id,
        author_id=body.author_id,
        author_name=author_name,
        author_role=body.author_role,
        content=body.content,
    )
    db.add(comment)

    # notify task assignee (by user id) if commenter is not the assignee
    if task.assignee_id and task.assignee_id != body.author_id:
        assignee_tm = db.query(TeamMember).filter(TeamMember.id == task.assignee_id).first()
        if assignee_tm:
            u = user_by_handle(db, assignee_tm.handle)
            if u:
                notif = Notification(
                    recipient_id=u.id,
                    notif_title="New comment",
                    message=f'{author_name} commented on "{task.name}"',
                    type="COMMENT",
                )
                db.add(notif)

    db.commit()
    db.refresh(comment)
    return comment