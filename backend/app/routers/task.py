import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Notification,
    SubTask,
    Task,
    TaskLog,
    TaskPermission,
    TaskStatus,
    TaskSubmission,
    TeamMember,
)
from app.team_access import (
    is_supervisor_row,
    member_for_handle,
    norm_handle,
    notify_user,
    supervisor_member_for_team,
    user_by_handle,
)
from app.schemas.task import (
    SubTaskCreate,
    SubTaskOut,
    SubTaskUpdate,
    TaskCreate,
    TaskLogOut,
    TaskOut,
    TaskPermissionCreate,
    TaskPermissionOut,
    TaskSubmissionOut,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

_SUBMISSIONS_FS = Path(__file__).resolve().parent.parent / "uploads" / "task_submissions"
_UPLOADS_ROOT = Path(__file__).resolve().parent.parent / "uploads"
_MAX_SUBMISSION_BYTES = 25 * 1024 * 1024
_PUBLIC_API = os.getenv("PUBLIC_API_URL", "http://127.0.0.1:8001").rstrip("/")


def _submission_to_out(row: TaskSubmission) -> TaskSubmissionOut:
    file_url = None
    if row.stored_path:
        file_url = f"{_PUBLIC_API}/tasks/submissions/{row.id}/file"
    return TaskSubmissionOut(
        id=row.id,
        task_id=row.task_id,
        submitter_handle=row.submitter_handle,
        title=row.title,
        description=row.description,
        original_filename=row.original_filename,
        file_url=file_url,
        file_size=row.file_size,
        created_at=row.created_at,
    )


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
    task = Task(**payload.model_dump(exclude={"creator_handle"}))
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


@router.get("/submissions/{submission_id}/file")
def download_submission_file(submission_id: int, db: Session = Depends(get_db)):
    """Stream the uploaded file with correct MIME type (view PDF in browser)."""
    row = db.query(TaskSubmission).filter(TaskSubmission.id == submission_id).first()
    if not row or not row.stored_path:
        raise HTTPException(status_code=404, detail="No file for this submission")
    rel = row.stored_path.replace("/", os.sep)
    full_path = (_UPLOADS_ROOT / rel).resolve()
    try:
        full_path.relative_to(_UPLOADS_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="File missing on disk")
    media = row.content_type or "application/octet-stream"
    name = row.original_filename or full_path.name
    return FileResponse(
        path=str(full_path),
        filename=name,
        media_type=media,
        content_disposition_type="inline",
    )


@router.get("/{task_id}/submissions", response_model=list[TaskSubmissionOut])
def list_task_submissions(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    rows = (
        db.query(TaskSubmission)
        .filter(TaskSubmission.task_id == task_id)
        .order_by(TaskSubmission.created_at.desc())
        .all()
    )
    return [_submission_to_out(r) for r in rows]


@router.post("/{task_id}/submissions", response_model=TaskSubmissionOut)
def create_task_submission(
    task_id: int,
    title: str = Form(...),
    description: str = Form(""),
    submitter_handle: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.closed:
        raise HTTPException(
            status_code=403,
            detail="This task is completed; further submissions are not allowed.",
        )
    member = member_for_handle(db, task.team_id, submitter_handle)
    if not member:
        raise HTTPException(status_code=403, detail="You are not a member of this team")
    if task.assignee_id is None or member.id != task.assignee_id:
        raise HTTPException(status_code=403, detail="Only the assigned member can submit work for this task")
    if not title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    stored = None
    orig = None
    ctype = None
    fsize = None
    if file is not None and file.filename:
        _SUBMISSIONS_FS.mkdir(parents=True, exist_ok=True)
        fn = file.filename
        suffix = ""
        if "." in fn:
            ext = fn.rsplit(".", 1)[-1].lower()
            if ext.isalnum() and len(ext) <= 12:
                suffix = "." + ext
        key = f"{uuid.uuid4().hex}{suffix}"
        dest = _SUBMISSIONS_FS / key
        content = file.file.read()
        if len(content) > _MAX_SUBMISSION_BYTES:
            raise HTTPException(status_code=413, detail="File too large (max 25MB)")
        dest.write_bytes(content)
        stored = f"task_submissions/{key}"
        orig = fn
        ctype = file.content_type or "application/octet-stream"
        fsize = len(content)

    row = TaskSubmission(
        task_id=task_id,
        submitter_member_id=member.id,
        submitter_handle=member.handle,
        title=title.strip(),
        description=(description or "").strip(),
        stored_path=stored,
        original_filename=orig,
        content_type=ctype,
        file_size=fsize,
    )
    db.add(row)
    db.flush()
    _create_log(
        db,
        task_id,
        "submit_work",
        member.handle,
        f'Submitted: "{title.strip()}"' + (f" (file: {orig})" if orig else ""),
    )
    sup = supervisor_member_for_team(db, task.team_id)
    if sup is not None and sup.id != member.id:
        u = user_by_handle(db, sup.handle)
        if u:
            _push_notification(
                db,
                u.id,
                "Work submitted",
                f'@{member.handle} submitted "{title.strip()}" on task "{task.name}"',
                "WORK_SUBMITTED",
            )
    db.commit()
    db.refresh(row)
    return _submission_to_out(row)


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: int,
    supervisor_handle: str = Query(..., description="Logged-in supervisor User ID"),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    m = member_for_handle(db, task.team_id, supervisor_handle)
    if not is_supervisor_row(m):
        raise HTTPException(status_code=403, detail="Only the team supervisor can complete this task")
    if task.grade is None:
        raise HTTPException(
            status_code=400,
            detail="Save a grade before completing this task.",
        )
    if task.closed:
        raise HTTPException(status_code=400, detail="Task is already completed")
    task.closed = True
    task.status = TaskStatus.done
    _create_log(
        db,
        task.id,
        "complete_task",
        m.handle,
        "Task closed by supervisor; submissions disabled.",
    )
    db.commit()
    db.refresh(task)
    return task


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
    if task.closed:
        raise HTTPException(status_code=400, detail="This task is completed and cannot be edited.")

    old_assignee = task.assignee_id
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "status" and value is not None:
            value = TaskStatus(value) if isinstance(value, str) else value
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
    if task.closed:
        raise HTTPException(status_code=400, detail="This task is completed.")
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
    if task.closed:
        raise HTTPException(status_code=400, detail="This task is completed.")
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
    task = db.query(Task).filter(Task.id == subtask.task_id).first()
    if task and task.closed:
        raise HTTPException(status_code=400, detail="This task is completed.")
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