from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    notifId: int
    recipient_id: int
    notifTitle: str
    message: str
    type: str
    isRead: bool
    createdAt: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, n: Notification):
        return cls(
            notifId=n.id,
            recipient_id=n.recipient_id,
            notifTitle=n.notif_title,
            message=n.message,
            type=n.type,
            isRead=n.is_read,
            createdAt=n.created_at.strftime("%b %d, %Y · %H:%M"),
        )


@router.get("/{recipient_id}")
def get_notifications(recipient_id: int, db: Session = Depends(get_db)):
    notifs = (
        db.query(Notification)
        .filter(Notification.recipient_id == recipient_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [NotificationOut.from_orm_custom(n) for n in notifs]


@router.patch("/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"ok": True}


@router.patch("/read-all")
def mark_all_read(recipient_id: int = Query(...), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.recipient_id == recipient_id,
        Notification.is_read.is_(False),
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}