from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user import ChangePasswordRequest, UpdateProfileRequest, UserResponse
from app.token import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["profile"])


@router.get("/{handle}", response_model=UserResponse)
def get_profile(handle: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == handle).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{handle}", response_model=UserResponse)
def update_profile(handle: str, body: UpdateProfileRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == handle).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.name is not None:
        user.name = body.name
    if body.description is not None:
        user.description = body.description
    if body.theme is not None:
        user.theme = body.theme.value
    if body.email is not None:
        existing = db.query(User).filter(User.email == body.email, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = body.email

    if body.handle is not None and body.handle != user.handle:
        if user.handle_changes_left <= 0:
            raise HTTPException(status_code=400, detail="No User ID changes remaining")
        conflict = db.query(User).filter(User.handle == body.handle).first()
        if conflict:
            raise HTTPException(status_code=400, detail="User ID already taken")
        user.handle = body.handle
        user.handle_changes_left -= 1

    db.commit()
    db.refresh(user)
    return user


@router.post("/{handle}/avatar", response_model=UserResponse)
async def upload_avatar(handle: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == handle).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG or WEBP allowed")
    fake_url = f"https://cdn.example.com/avatars/{handle}.jpg"
    user.profile_image = fake_url
    db.commit()
    db.refresh(user)
    return user


@router.post("/{handle}/change-password")
def change_password(handle: str, body: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == handle).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    user.refresh_token = None
    db.commit()
    return {"detail": "Password changed successfully"}