from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PlanningActivity, Task, TaskStatus, TeamMember
from app.schemas.planning import PlanningCreate, PlanningOut

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("", response_model=PlanningOut)
def create_activity(payload: PlanningCreate, db: Session = Depends(get_db)):
    activity = PlanningActivity(**payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("", response_model=list[PlanningOut])
def list_activities(team_id: int, category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(PlanningActivity).filter(PlanningActivity.team_id == team_id)
    if category:
        query = query.filter(PlanningActivity.category == category)
    return query.order_by(PlanningActivity.timeline_start.asc()).all()


@router.get("/performance")
def team_performance(team_id: int, db: Session = Depends(get_db)):
    task_totals = (
        db.query(Task.assignee_id, func.count(Task.id))
        .filter(Task.team_id == team_id, Task.assignee_id.isnot(None))
        .group_by(Task.assignee_id)
        .all()
    )
    completed = (
        db.query(Task.assignee_id, func.count(Task.id))
        .filter(Task.team_id == team_id, Task.assignee_id.isnot(None), Task.status == TaskStatus.done)
        .group_by(Task.assignee_id)
        .all()
    )
    grade_avg = (
        db.query(Task.assignee_id, func.avg(Task.grade))
        .filter(Task.team_id == team_id, Task.assignee_id.isnot(None), Task.grade.isnot(None))
        .group_by(Task.assignee_id)
        .all()
    )
    members = {m.id: m for m in db.query(TeamMember).filter(TeamMember.team_id == team_id).all()}
    completed_map = {mid: cnt for mid, cnt in completed}
    grade_map = {mid: float(avg) for mid, avg in grade_avg}

    result = []
    for assignee_id, total in task_totals:
        member = members.get(assignee_id)
        if not member:
            continue
        done_count = completed_map.get(assignee_id, 0)
        result.append(
            {
                "member_id": assignee_id,
                "member_name": member.display_name,
                "assigned_tasks": total,
                "completed_tasks": done_count,
                "completion_rate": round((done_count / total) * 100, 2) if total else 0,
                "avg_grade": grade_map.get(assignee_id),
            }
        )
    return result
