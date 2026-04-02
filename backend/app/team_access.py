"""Team role and handle helpers (Jira_Copycat)."""

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Notification, TeamMember, User

SUPERVISOR_ROLES = frozenset({"supervisor", "lead"})


def norm_handle(h: str | None) -> str:
    if not h:
        return ""
    s = str(h).strip()
    if s.startswith("@"):
        s = s[1:].strip()
    return s


def user_by_handle(db: Session, handle: str) -> User | None:
    nh = norm_handle(handle).lower()
    if not nh:
        return None
    return db.query(User).filter(func.lower(User.handle) == nh).first()


def member_for_handle(db: Session, team_id: int, handle: str | None) -> TeamMember | None:
    nh = norm_handle(handle).lower()
    if not team_id or not nh:
        return None
    return (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            func.lower(TeamMember.handle) == nh,
            TeamMember.is_active.is_(True),
        )
        .first()
    )


def is_supervisor_row(m: TeamMember | None) -> bool:
    return m is not None and m.role_name in SUPERVISOR_ROLES


def assert_supervisor(db: Session, team_id: int, handle: str | None) -> TeamMember:
    m = member_for_handle(db, team_id, handle)
    if not is_supervisor_row(m):
        raise HTTPException(status_code=403, detail="Only the team supervisor can do this")
    return m


def supervisor_member_for_team(db: Session, team_id: int) -> TeamMember | None:
    return (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.role_name.in_(list(SUPERVISOR_ROLES)),
            TeamMember.is_active.is_(True),
        )
        .first()
    )


def notify_user(db: Session, user_id: int, title: str, message: str, ntype: str) -> None:
    db.add(
        Notification(
            recipient_id=user_id,
            notif_title=title,
            message=message,
            type=ntype,
        )
    )
