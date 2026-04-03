import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

_explicit = os.getenv("DATABASE_URL", "").strip()
# Default SQLite for local dev; set USE_SQLITE=false (or 0/no) to use MySQL defaults below.
_use_sqlite = os.getenv("USE_SQLITE", "true").lower() not in ("0", "false", "no")

if _explicit:
    DATABASE_URL = _explicit
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=not DATABASE_URL.startswith("sqlite"),
        **({"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}),
    )
elif _use_sqlite:
    DATABASE_URL = "sqlite:///./local.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DB = os.getenv("MYSQL_DB", "project_db")
    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_schema():
    """Add columns missing from older DB files (SQLite only)."""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
        cols = {r[1] for r in rows}
        if "closed" not in cols:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN closed BOOLEAN NOT NULL DEFAULT 0"))


def ensure_mysql_tasks_closed_column():
    if str(engine.url).startswith("sqlite"):
        return
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN closed BOOLEAN NOT NULL DEFAULT 0"))
    except Exception:
        pass
