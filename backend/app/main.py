from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, ensure_mysql_tasks_closed_column, ensure_sqlite_schema
from app.routers import auth, comment, notification, planning, profile, task, team

Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()
ensure_mysql_tasks_closed_column()

_UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
(_UPLOADS_DIR / "task_submissions").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="FlowBoard API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(team.router)
app.include_router(task.router)
app.include_router(comment.router)
app.include_router(notification.router)
app.include_router(planning.router)

app.mount("/uploads", StaticFiles(directory=str(_UPLOADS_DIR)), name="uploads")


@app.get("/")
def health():
    return {"status": "ok"}