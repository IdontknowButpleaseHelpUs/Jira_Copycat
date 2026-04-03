from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PlanningActivity, Task, TaskStatus, TeamMember
from app.schemas.planning import PlanningCreate, PlanningOut
from app.team_access import assert_supervisor

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("", response_model=PlanningOut)
def create_activity(payload: PlanningCreate, db: Session = Depends(get_db)):
    assert_supervisor(db, payload.team_id, payload.member_handle)
    data = payload.model_dump(exclude={"member_handle"})
    activity = PlanningActivity(**data)
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
    members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.is_active.is_(True),
    ).all()

    task_totals = {
        mid: cnt for mid, cnt in
        db.query(Task.assignee_id, func.count(Task.id))
        .filter(Task.team_id == team_id, Task.assignee_id.isnot(None))
        .group_by(Task.assignee_id).all()
    }
    completed = {
        mid: cnt for mid, cnt in
        db.query(Task.assignee_id, func.count(Task.id))
        .filter(Task.team_id == team_id, Task.status == TaskStatus.done, Task.assignee_id.isnot(None))
        .group_by(Task.assignee_id).all()
    }
    grade_avg = {
        mid: float(avg) for mid, avg in
        db.query(Task.assignee_id, func.avg(Task.grade))
        .filter(Task.team_id == team_id, Task.grade.isnot(None), Task.assignee_id.isnot(None))
        .group_by(Task.assignee_id).all()
    }

    result = []
    for member in members:
        total = task_totals.get(member.id, 0)
        done_count = completed.get(member.id, 0)
        result.append(
            {
                "member_id": member.id,
                "member_name": member.display_name,
                "assigned_tasks": total,
                "completed_tasks": done_count,
                "completion_rate": round((done_count / total) * 100, 2) if total else 0,
                "avg_grade": grade_avg.get(member.id),
            }
        )
    return result