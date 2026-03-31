"""Mock API server for comment demo."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List
import uvicorn

app = FastAPI()

# Enable CORS for Reflex frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
class Comment(BaseModel):
    id: int
    authorId: int
    authorName: str
    authorRole: str
    content: str
    createdAt: str

class Notification(BaseModel):
    notifId: int
    recipientId: int
    notifTitle: str
    message: str
    type: str
    isRead: bool
    createdAt: str

# Sample comments
mock_comments = {
    1: [
        Comment(
            id=1,
            authorId=1,
            authorName="Alice Johnson",
            authorRole="MEMBER",
            content="Great project! Really impressive work on the implementation.",
            createdAt="2024-01-15T10:30:00"
        ),
        Comment(
            id=2,
            authorId=2,
            authorName="Bob Smith",
            authorRole="SUPERVISOR",
            content="I love the design and functionality. Good job!",
            createdAt="2024-01-15T11:45:00"
        ),
        Comment(
            id=3,
            authorId=3,
            authorName="Charlie Davis",
            authorRole="MEMBER",
            content="This could be really useful for our team workflow.",
            createdAt="2024-01-15T14:20:00"
        ),
    ]
}

# Sample notifications
mock_notifications = {
    1: [
        Notification(
            notifId=1,
            recipientId=1,
            notifTitle="Task Assigned",
            message="You have been assigned to 'Fix login bug'",
            type="TASK_ASSIGNED",
            isRead=False,
            createdAt="2024-01-15T09:30:00"
        ),
        Notification(
            notifId=2,
            recipientId=1,
            notifTitle="Deadline Approaching",
            message="Project deadline is in 2 days",
            type="DEADLINE",
            isRead=False,
            createdAt="2024-01-15T10:15:00"
        ),
        Notification(
            notifId=3,
            recipientId=1,
            notifTitle="Work Returned",
            message="Your submission needs revision",
            type="WORK_RETURNED",
            isRead=True,
            createdAt="2024-01-14T16:45:00"
        ),
    ]
}

comment_counter = 4  # Next comment ID

@app.get("/tasks/{task_id}/comments")
async def get_comments(task_id: int):
    """Get comments for a specific task."""
    comments = mock_comments.get(task_id, [])
    return [comment.dict() for comment in comments]

@app.post("/tasks/{task_id}/comments")
async def create_comment(task_id: int, comment_data: dict):
    """Create a new comment."""
    global comment_counter
    
    new_comment = Comment(
        id=comment_counter,
        authorId=comment_data["authorId"],
        authorName=f"User {comment_data['authorId']}",
        authorRole=comment_data["authorRole"],
        content=comment_data["content"],
        createdAt=datetime.now().isoformat()
    )
    
    comment_counter += 1
    
    if task_id not in mock_comments:
        mock_comments[task_id] = []
    
    mock_comments[task_id].append(new_comment)
    return new_comment.dict()

# Notification endpoints
@app.get("/notifications/{recipient_id}")
async def get_notifications(recipient_id: int):
    """Get notifications for a specific user."""
    notifications = mock_notifications.get(recipient_id, [])
    return [n.dict() for n in notifications]

@app.patch("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int):
    """Mark a notification as read."""
    for recipient_id, notifications in mock_notifications.items():
        for notif in notifications:
            if notif.notifId == notif_id:
                notif.isRead = True
                return {"status": "ok"}
    return {"status": "not found"}

@app.patch("/notifications/read-all")
async def mark_all_read(recipient_id: int):
    """Mark all notifications as read for a user."""
    notifications = mock_notifications.get(recipient_id, [])
    for notif in notifications:
        notif.isRead = True
    return {"status": "ok"}

if __name__ == "__main__":
    print("Starting mock API server on http://localhost:8001")
    uvicorn.run(app, host="localhost", port=8001)
