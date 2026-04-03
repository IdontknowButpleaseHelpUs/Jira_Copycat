from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JoinRequestStatus, Team, TeamJoinRequest, TeamMember
from app.schemas.team import InviteMemberRequest, JoinRequestOut, JoinTeamRequest, TeamCreate, TeamMemberOut, TeamOut
from app.team_access import (
    assert_supervisor,
    member_for_handle,
    norm_handle,
    notify_user,
    supervisor_member_for_team,
    user_by_handle,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamOut)
def create_team(payload: TeamCreate, db: Session = Depends(get_db)):
    exists = db.query(Team).filter((Team.name == payload.name) | (Team.join_code == payload.join_code)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Team name or join code already exists")
    team = Team(
        name=payload.name,
        description=payload.description,
        join_code=payload.join_code,
    )
    db.add(team)
    db.flush()
    if payload.creator_handle:
        ch = norm_handle(payload.creator_handle)
        creator_user = user_by_handle(db, ch)
        if not creator_user:
            raise HTTPException(status_code=400, detail="Creator handle must be a registered user")
        existing_owner = db.query(TeamMember).filter(
            TeamMember.team_id == team.id,
            func.lower(TeamMember.handle) == creator_user.handle.lower(),
            TeamMember.is_active.is_(True),
        ).first()
        if not existing_owner:
            db.add(
                TeamMember(
                    team_id=team.id,
                    display_name=(payload.creator_display_name or creator_user.name),
                    handle=creator_user.handle,
                    role_name="supervisor",
                )
            )
    db.commit()
    db.refresh(team)
    return team


@router.get("", response_model=list[TeamOut])
def list_teams(handle: str | None = Query(default=None), db: Session = Depends(get_db)):
    if not handle:
        return []
    nh = norm_handle(handle).lower()
    return (
        db.query(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(func.lower(TeamMember.handle) == nh, TeamMember.is_active.is_(True))
        .all()
    )


@router.post("/join/{join_code}", response_model=JoinRequestOut)
def request_join_team(join_code: str, payload: JoinTeamRequest, db: Session = Depends(get_db)):
    nh = norm_handle(payload.handle)
    acc = user_by_handle(db, nh)
    if not acc:
        raise HTTPException(status_code=400, detail="User ID must match a registered account")
    team = db.query(Team).filter(Team.join_code == join_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Join code not found")
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team.id,
        func.lower(TeamMember.handle) == nh.lower(),
        TeamMember.is_active.is_(True),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already joined this team")
    pending = (
        db.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.team_id == team.id,
            func.lower(TeamJoinRequest.handle) == nh.lower(),
            TeamJoinRequest.status == JoinRequestStatus.pending,
        )
        .first()
    )
    if pending:
        raise HTTPException(status_code=400, detail="You already have a pending request for this team")
    jr = TeamJoinRequest(
        team_id=team.id,
        handle=acc.handle,
        display_name=payload.display_name.strip(),
        status=JoinRequestStatus.pending,
    )
    db.add(jr)
    db.flush()
    sup = supervisor_member_for_team(db, team.id)
    if sup:
        u = user_by_handle(db, sup.handle)
        if u:
            notify_user(
                db,
                u.id,
                "Join request",
                f'{payload.display_name} (@{acc.handle}) asked to join "{team.name}".',
                "JOIN_REQUEST",
            )
    db.commit()
    db.refresh(jr)
    return jr


@router.get("/{team_id}/join-requests", response_model=list[JoinRequestOut])
def list_join_requests(
    team_id: int,
    supervisor_handle: str = Query(...),
    db: Session = Depends(get_db),
):
    assert_supervisor(db, team_id, supervisor_handle)
    rows = (
        db.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.team_id == team_id,
            TeamJoinRequest.status == JoinRequestStatus.pending,
        )
        .order_by(TeamJoinRequest.created_at.desc())
        .all()
    )
    return rows


@router.post("/{team_id}/join-requests/{request_id}/approve", response_model=TeamMemberOut)
def approve_join_request(
    team_id: int,
    request_id: int,
    supervisor_handle: str = Query(...),
    db: Session = Depends(get_db),
):
    assert_supervisor(db, team_id, supervisor_handle)
    jr = (
        db.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.id == request_id,
            TeamJoinRequest.team_id == team_id,
            TeamJoinRequest.status == JoinRequestStatus.pending,
        )
        .first()
    )
    if not jr:
        raise HTTPException(status_code=404, detail="Pending join request not found")
    dup = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        func.lower(TeamMember.handle) == jr.handle.lower(),
        TeamMember.is_active.is_(True),
    ).first()
    if dup:
        jr.status = JoinRequestStatus.rejected
        jr.decided_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail="User is already a member")
    member = TeamMember(
        team_id=team_id,
        display_name=jr.display_name,
        handle=jr.handle,
        role_name="member",
    )
    db.add(member)
    jr.status = JoinRequestStatus.approved
    jr.decided_at = datetime.utcnow()
    db.flush()
    invited = user_by_handle(db, jr.handle)
    if invited:
        t = db.query(Team).filter(Team.id == team_id).first()
        tname = t.name if t else "the team"
        notify_user(
            db,
            invited.id,
            "Welcome to the team",
            f'You were approved for "{tname}".',
            "TASK_ASSIGNED",
        )
    db.commit()
    db.refresh(member)
    return member


@router.post("/{team_id}/join-requests/{request_id}/reject")
def reject_join_request(
    team_id: int,
    request_id: int,
    supervisor_handle: str = Query(...),
    db: Session = Depends(get_db),
):
    assert_supervisor(db, team_id, supervisor_handle)
    jr = (
        db.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.id == request_id,
            TeamJoinRequest.team_id == team_id,
            TeamJoinRequest.status == JoinRequestStatus.pending,
        )
        .first()
    )
    if not jr:
        raise HTTPException(status_code=404, detail="Pending join request not found")
    jr.status = JoinRequestStatus.rejected
    jr.decided_at = datetime.utcnow()
    db.commit()
    return {"message": "Join request rejected"}


@router.post("/members", response_model=TeamMemberOut)
def invite_member(payload: InviteMemberRequest, db: Session = Depends(get_db)):
    assert_supervisor(db, payload.team_id, payload.inviter_handle)
    team = db.query(Team).filter(Team.id == payload.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    ih = norm_handle(payload.invitee_handle)
    acc = user_by_handle(db, ih)
    if not acc:
        raise HTTPException(status_code=400, detail="No registered user with this User ID")
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == payload.team_id,
        func.lower(TeamMember.handle) == ih.lower(),
        TeamMember.is_active.is_(True),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member already in this team")
    member = TeamMember(
        team_id=payload.team_id,
        display_name=acc.name,
        handle=acc.handle,
        role_name="member",
    )
    db.add(member)
    db.flush()
    notify_user(
        db,
        acc.id,
        "Added to team",
        f'You have been added to "{team.name}"',
        "TASK_ASSIGNED",
    )
    db.commit()
    db.refresh(member)
    return member


@router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_members(team_id: int, db: Session = Depends(get_db)):
    return db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.is_active.is_(True)).all()


@router.delete("/members/{member_id}")
def remove_member(
    member_id: int,
    supervisor_handle: str = Query(...),
    db: Session = Depends(get_db),
):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    assert_supervisor(db, member.team_id, supervisor_handle)
    if member.role_name in ("supervisor", "lead"):
        raise HTTPException(status_code=400, detail="Cannot remove the team supervisor")
    member.is_active = False
    db.commit()
    return {"message": "Member removed"}
