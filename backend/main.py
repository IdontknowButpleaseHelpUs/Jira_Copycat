from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()
import os
import traceback

from backend.models.user import User
from backend.api.auth import router as auth_router
from backend.api.profile import router as profile_router

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://n12e0n3_db_user:abcd1234@m0.t3lbywi.mongodb.net/?appName=M0")
DB_NAME = os.getenv("DB_NAME", "jira_copycat")

app = FastAPI(title="Jira Copycat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("ERROR:", traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.on_event("startup")
async def startup():
    client = AsyncIOMotorClient(MONGO_URI)
    database = client[DB_NAME]
    await init_beanie(
        database=database,
        document_models=[User],
    )


app.include_router(auth_router)
app.include_router(profile_router)


@app.get("/health")
async def health():
    return {"status": "ok"}