from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import Course, CourseEnrollment, Team, TeamMember, User, CourseType
from app.schemas.course import CourseCreate, CourseOut, CourseEnrollmentOut

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/my", response_model=list[CourseOut])
def list_my_courses(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List all courses the current user is enrolled in."""
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == user_id)
        .all()
    )
    course_ids = [e.course_id for e in enrollments]
    if not course_ids:
        return []
    courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
    return courses


@router.get("/type/{course_type}", response_model=list[CourseOut])
def list_courses_by_type(
    course_type: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List courses by type (academic or project) for enrolled user."""
    # Get user's enrolled course IDs
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == user_id)
        .all()
    )
    course_ids = [e.course_id for e in enrollments]
    if not course_ids:
        return []

    # Filter by type
    try:
        ct = CourseType(course_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid course type")

    courses = (
        db.query(Course)
        .filter(Course.id.in_(course_ids), Course.course_type == ct)
        .all()
    )
    return courses


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get a single course by ID (if user is enrolled)."""
    # Check enrollment
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == user_id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course",
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/teams", response_model=list[dict])
def get_course_teams(
    course_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get all teams in a course that the user is a member of."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    # Check enrollment
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == user_id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course",
        )

    # Get teams in this course where user is a member
    teams = (
        db.query(Team)
        .join(TeamMember, Team.id == TeamMember.team_id)
        .filter(
            Team.course_id == course_id,
            TeamMember.handle == user.handle,
            TeamMember.is_active == True,
        )
        .all()
    )

    # Format response
    result = []
    for team in teams:
        member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team.id, TeamMember.handle == user.handle)
            .first()
        )
        result.append({
            "id": team.id,
            "course_id": team.course_id,
            "name": team.name,
            "description": team.description,
            "join_code": team.join_code,
            "my_role": member.role_name if member else "member",
        })
    return result
