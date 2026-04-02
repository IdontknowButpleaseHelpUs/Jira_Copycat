from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Team, TeamMember
from app.schemas.team import TeamCreate, TeamMemberCreate, TeamMemberJoin, TeamMemberOut, TeamOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamOut)
def create_team(payload: TeamCreate, db: Session = Depends(get_db)):
    exists = db.query(Team).filter((Team.name == payload.name) | (Team.join_code == payload.join_code)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Team name or join code already exists")
    team = Team(**payload.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()


@router.post("/join/{join_code}", response_model=TeamMemberOut)
def join_team(join_code: str, payload: TeamMemberJoin, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.join_code == join_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Join code not found")
    member = TeamMember(
        team_id=team.id,
        display_name=payload.display_name,
        handle=payload.handle,
        role_name=payload.role_name,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.post("/members", response_model=TeamMemberOut)
def add_member(payload: TeamMemberCreate, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == payload.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    member = TeamMember(**payload.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_members(team_id: int, db: Session = Depends(get_db)):
    return db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.is_active.is_(True)).all()


@router.delete("/members/{member_id}")
def remove_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_active = False
    db.commit()
    return {"message": "Member removed"}