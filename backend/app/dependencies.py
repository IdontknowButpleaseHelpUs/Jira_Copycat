from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.tokens import decode_token


def _user_id_from_handle(db: Session, handle: str) -> int:
    user = db.query(User).filter(User.handle == handle).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return int(user.id)


def get_current_user_id(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_user_handle: str | None = Header(default=None, alias="X-User-Handle"),
):
    """Resolve the current user id.

    Supports:
    - Authorization: Bearer <access_token> where token.sub == user handle
    - X-User-Handle header
    - ?handle=<user_handle> query parameter

    This keeps the API compatible with the existing frontend pattern while allowing
    proper token auth.
    """

    token = None
    if authorization:
        parts = authorization.strip().split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()

    handle = None
    if token:
        handle = decode_token(token, expected_type="access")
    elif x_user_handle:
        handle = x_user_handle.strip()
    else:
        qp_handle = request.query_params.get("handle")
        if qp_handle:
            handle = qp_handle.strip()

    if not handle:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return _user_id_from_handle(db, handle)
