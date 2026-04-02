from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification, SubTask, Task, TaskLog, TaskPermission, TaskStatus, TeamMember
from app.team_access import is_supervisor_row, member_for_handle, norm_handle, notify_user, user_by_handle
from app.schemas.task import (
    SubTaskCreate,
    SubTaskOut,
    SubTaskUpdate,
    TaskCreate,
    TaskLogOut,
    TaskOut,
    TaskPermissionCreate,
    TaskPermissionOut,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _create_log(db: Session, task_id: int, action: str, actor: str, details: str):
    db.add(TaskLog(task_id=task_id, action=action, actor=actor, details=details))


def _push_notification(db: Session, recipient_id: int, title: str, message: str, ntype: str):
    db.add(Notification(
        recipient_id=recipient_id,
        notif_title=title,
        message=message,
        type=ntype,
    ))


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    if not payload.creator_handle:
        raise HTTPException(status_code=400, detail="creator_handle is required")
    membership = member_for_handle(db, payload.team_id, payload.creator_handle)
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this team")
    if not is_supervisor_row(membership):
        raise HTTPException(status_code=403, detail="Only the team supervisor can create tasks")
    task = Task(**payload.model_dump())
    db.add(task)
    db.flush()
    _create_log(db, task.id, "create_task", payload.creator_name, f"Task created with status {task.status.value}")
    # notify assignee if set at creation
    if task.assignee_id:
        assignee = db.query(TeamMember).filter(TeamMember.id == task.assignee_id).first()
        if assignee:
            u = user_by_handle(db, assignee.handle)
            if u:
                _push_notification(
                    db,
                    u.id,
                    "Task assigned",
                    f'You were assigned "{task.name}"',
                    "TASK_ASSIGNED",
                )
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    team_id: int | None = None,
    status: TaskStatus | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if team_id:
        query = query.filter(Task.team_id == team_id)
    if status:
        query = query.filter(Task.status == status)
    if category:
        query = query.filter(Task.category == category)
    return query.order_by(Task.deadline.is_(None), Task.deadline.asc()).all()


@router.get("/kanban", response_model=dict[str, list[TaskOut]])
def kanban_view(team_id: int = Query(...), db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.team_id == team_id).all()
    board = {s.value: [] for s in TaskStatus}
    for task in tasks:
        board[task.status.value].append(task)
    return board


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, actor: str = "system", db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_assignee = task.assignee_id
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    # notify new assignee if changed
    if payload.assignee_id is not None and payload.assignee_id != old_assignee and payload.assignee_id:
        assignee = db.query(TeamMember).filter(TeamMember.id == payload.assignee_id).first()
        if assignee:
            u = user_by_handle(db, assignee.handle)
            if u:
                _push_notification(
                    db,
                    u.id,
                    "Task assigned",
                    f'You were assigned "{task.name}"',
                    "TASK_ASSIGNED",
                )

    _create_log(db, task.id, "update_task", actor, "Task updated")
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/return", response_model=TaskOut)
def return_task(
    task_id: int,
    reason: str = Query(..., min_length=1),
    actor: str = Query("reviewer"),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.returned
    task.rejection_flag = True
    task.rejection_reason = reason
    _create_log(db, task.id, "return_task", actor, reason)
    # notify assignee
    if task.assignee_id:
        assignee = db.query(TeamMember).filter(TeamMember.id == task.assignee_id).first()
        if assignee:
            u = user_by_handle(db, assignee.handle)
            if u:
                _push_notification(
                    db,
                    u.id,
                    "Work returned",
                    f'"{task.name}" was returned: {reason[:80]}',
                    "WORK_RETURNED",
                )
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/subtasks", response_model=SubTaskOut)
def create_subtask(
    task_id: int,
    payload: SubTaskCreate,
    creator_handle: str = Query(..., description="Handle of the member creating the subtask"),
    db: Session = Depends(get_db),
):
    if payload.task_id != task_id:
        raise HTTPException(status_code=400, detail="task_id mismatch")
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    actor = member_for_handle(db, task.team_id, creator_handle)
    if not actor:
        raise HTTPException(status_code=403, detail="You are not a member of this team")
    subtask = SubTask(**payload.model_dump())
    db.add(subtask)
    label = norm_handle(creator_handle) or actor.handle
    _create_log(db, task_id, "create_subtask", label, payload.title)
    db.flush()
    others = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == task.team_id, TeamMember.is_active.is_(True))
        .all()
    )
    for m in others:
        if m.id == actor.id:
            continue
        u = user_by_handle(db, m.handle)
        if u:
            notify_user(
                db,
                u.id,
                "New subtask",
                f"@{label} created a subtask called {payload.title}",
                "SUBTASK_CREATED",
            )
    db.commit()
    db.refresh(subtask)
    return subtask


@router.get("/{task_id}/subtasks", response_model=list[SubTaskOut])
def list_subtasks(task_id: int, db: Session = Depends(get_db)):
    return db.query(SubTask).filter(SubTask.task_id == task_id).all()


@router.patch("/subtasks/{subtask_id}", response_model=SubTaskOut)
def update_subtask(subtask_id: int, payload: SubTaskUpdate, db: Session = Depends(get_db)):
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    subtask.is_done = payload.is_done
    db.commit()
    db.refresh(subtask)
    return subtask


@router.post("/{task_id}/permissions", response_model=TaskPermissionOut)
def add_permission(task_id: int, payload: TaskPermissionCreate, db: Session = Depends(get_db)):
    if payload.task_id != task_id:
        raise HTTPException(status_code=400, detail="task_id mismatch")
    permission = TaskPermission(**payload.model_dump())
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


@router.get("/{task_id}/permissions", response_model=list[TaskPermissionOut])
def list_permissions(task_id: int, db: Session = Depends(get_db)):
    return db.query(TaskPermission).filter(TaskPermission.task_id == task_id).all()


@router.get("/{task_id}/logs", response_model=list[TaskLogOut])
def task_logs(task_id: int, db: Session = Depends(get_db)):
    return db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.created_at.desc()).all()