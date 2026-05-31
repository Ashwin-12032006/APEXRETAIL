import os
import sqlite3
import threading
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Define database URL (/tmp on Vercel — serverless has no persistent disk)
_DEFAULT_SQLITE = (
    "sqlite:////tmp/store_intelligence.db"
    if os.getenv("VERCEL")
    else "sqlite:///d:/APEX RETAIL_KASH/store-intelligence/data/store_intelligence.db"
)
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_SQLITE)

# Serialize SQLite writes (simulator + ingest); WAL allows concurrent reads
db_write_lock = threading.Lock()


def _sqlite_file_path() -> str:
    return DATABASE_URL.replace("sqlite:///", "").replace("/", os.sep)


def bootstrap_sqlite() -> None:
    """Enable WAL once before any pooled connections (fixes 'database is locked' on reads)."""
    if "sqlite" not in DATABASE_URL:
        return
    path = _sqlite_file_path()
    if not os.path.isfile(path):
        return
    try:
        conn = sqlite3.connect(path, timeout=60)
        try:
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.commit()
        finally:
            conn.close()
    except sqlite3.OperationalError:
        # Another process (e.g. old uvicorn) holds the DB; skip — pool connect will retry WAL
        pass


bootstrap_sqlite()

# NullPool: fresh connection per request — works best with SQLite + background writer + WAL
_sqlite_connect_args = {"check_same_thread": False, "timeout": 60} if "sqlite" in DATABASE_URL else {}
_engine_kwargs = (
    {"connect_args": _sqlite_connect_args, "poolclass": NullPool}
    if "sqlite" in DATABASE_URL
    else {}
)
engine = create_engine(DATABASE_URL, **_engine_kwargs)

@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_connection, connection_record):
    if "sqlite" not in DATABASE_URL:
        return
    cursor = dbapi_connection.cursor()
    # busy_timeout first so subsequent pragmas can wait for the writer
    cursor.execute("PRAGMA busy_timeout=30000")
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass  # WAL may fail if DB is mid-write; next connection will retry
    cursor.close()

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
