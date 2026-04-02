from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, comment, notification, planning, profile, task, team

Base.metadata.create_all(bind=engine)

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


@app.get("/")
def health():
    return {"status": "ok"}