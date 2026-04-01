from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import aiosmtplib
from email.message import EmailMessage
import os
from backend.models.user import User
from backend.schemas.user import (
    RegisterRequest, LoginRequest, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from backend.app.token import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    create_reset_token, decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


async def send_reset_email(to_email: str, reset_url: str):
    message = EmailMessage()
    message["From"] = GMAIL_USER
    message["To"] = to_email
    message["Subject"] = "Password Reset Request"
    message.set_content(f"""
Hi,

You requested a password reset. Click the link below to reset your password:

{reset_url}

This link expires in 15 minutes.

If you didn't request this, ignore this email.
""")
    await aiosmtplib.send(
    message,
    hostname="smtp.gmail.com",
    port=587,
    username=GMAIL_USER,
    password=GMAIL_APP_PASSWORD,
    start_tls=True,
    sender=GMAIL_USER,      # add this
    recipients=[to_email],  # add this
)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest):
    if await User.find_one(User.email == body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        passwordHash=hash_password(body.password),
    )
    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    user.refresh_token = refresh
    await user.insert()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await User.find_one(User.email == body.email)
    if not user or not verify_password(body.password, user.passwordHash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    user.refresh_token = refresh
    await user.save()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", status_code=204)
async def logout(body: dict):
    email = body.get("email")
    user = await User.find_one(User.email == email)
    if user:
        user.refresh_token = None
        await user.save()


@router.post("/forgot-password", status_code=202)
async def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    user = await User.find_one(User.email == body.email)
    if user:
        token = create_reset_token(user.email)
        reset_url = f"http://localhost:3000/reset-password/{token}"
        background_tasks.add_task(send_reset_email, body.email, reset_url)
    return {"detail": "If this email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
async def reset_password(body: ResetPasswordRequest):
    email = decode_token(body.token, expected_type="reset")
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user.passwordHash = hash_password(body.new_password)
    user.refresh_token = None
    await user.save()
    return {"detail": "Password updated successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: dict):
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token required")

    email = decode_token(token, expected_type="refresh")
    user = await User.find_one(User.email == email)
    if not user or user.refresh_token != token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token(email)
    refresh = create_refresh_token(email)
    user.refresh_token = refresh
    await user.save()

    return TokenResponse(access_token=access, refresh_token=refresh)