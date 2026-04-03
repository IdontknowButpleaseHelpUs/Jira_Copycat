import logging
import os

import aiosmtplib
from email.message import EmailMessage
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.token import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def _send_reset_email(to_email: str, reset_url: str):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.warning(f"[EMAIL SKIP] No SMTP config. Reset URL: {reset_url}")
        return
    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = "Password Reset Request"
    msg.set_content(
        f"Hi,\n\nClick below to reset your password:\n\n{reset_url}\n\n"
        "This link expires in 15 minutes.\n\nIf you didn't request this, ignore this email."
    )
    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            username=GMAIL_USER,
            password=GMAIL_APP_PASSWORD,
            start_tls=True,
            sender=GMAIL_USER,
            recipients=[to_email],
        )
    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.handle == body.handle).first():
        raise HTTPException(status_code=400, detail="User ID already taken")
    if body.email:
        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        handle=body.handle,
        name=body.name,
        email=body.email or None,
        password_hash=hash_password(body.password),
    )
    access = create_access_token(user.handle)
    refresh = create_refresh_token(user.handle)
    user.refresh_token = refresh
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.handle == body.handle).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid User ID or password")
    access = create_access_token(user.handle)
    refresh = create_refresh_token(user.handle)
    user.refresh_token = refresh
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", status_code=204)
def logout(body: dict, db: Session = Depends(get_db)):
    handle = body.get("handle")
    user = db.query(User).filter(User.handle == handle).first()
    if user:
        user.refresh_token = None
        db.commit()


@router.post("/forgot-password", status_code=202)
async def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.handle == body.handle).first()
    if user and user.email:
        token = create_reset_token(user.handle)
        reset_url = f"{FRONTEND_URL}/reset-password/{token}"
        background_tasks.add_task(_send_reset_email, user.email, reset_url)
    return {"detail": "If this User ID has an email on file, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    handle = decode_token(body.token, expected_type="reset")
    user = db.query(User).filter(User.handle == handle).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    user.password_hash = hash_password(body.new_password)
    user.refresh_token = None
    db.commit()
    return {"detail": "Password updated successfully"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: dict, db: Session = Depends(get_db)):
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    handle = decode_token(token, expected_type="refresh")
    user = db.query(User).filter(User.handle == handle).first()
    if not user or user.refresh_token != token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access = create_access_token(handle)
    refresh = create_refresh_token(handle)
    user.refresh_token = refresh
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)