from fastapi import APIRouter, HTTPException, UploadFile, File
from backend.models.user import User
from backend.schemas.user import (
    UserResponse, UpdateProfileRequest, ChangePasswordRequest,
)
from backend.app.token import verify_password, hash_password

router = APIRouter(prefix="/users", tags=["profile"])


@router.get("/{email}", response_model=UserResponse)
async def get_profile(email: str):
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{email}", response_model=UserResponse)
async def update_profile(email: str, body: UpdateProfileRequest):
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.name is not None:
        user.name = body.name
    if body.description is not None:
        user.description = body.description
    if body.theme is not None:
        user.theme = body.theme

    await user.save()
    return user


@router.post("/{email}/avatar", response_model=UserResponse)
async def upload_avatar(email: str, file: UploadFile = File(...)):
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG or WEBP allowed")

    fake_url = f"https://cdn.example.com/avatars/{email}.jpg"
    user.profileImage = fake_url
    await user.save()
    return user


@router.post("/{email}/change-password")
async def change_password(email: str, body: ChangePasswordRequest):
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(body.current_password, user.passwordHash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.passwordHash = hash_password(body.new_password)
    user.refresh_token = None
    await user.save()
    return {"detail": "Password changed successfully"}