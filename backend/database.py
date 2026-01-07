import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def _normalize_sync_db_url(url: str) -> str:
    if not url:
        return "sqlite:///./dev_local.db"

    # Normalize common async drivers to sync URLs for runtime
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace(
        "postgres://", "postgresql://"
    )  # Fix for Railway/Heroku legacy format
    url = url.replace("sqlite+aiosqlite://", "sqlite://")

    # If someone provided a sync sqlite URL, keep it
    # If someone provided postgresql:// already, keep it
    return url


from sqlalchemy.pool import StaticPool  # noqa: E402

# NOTE: Environment should be loaded BEFORE importing this module via core.config.load_env_if_needed()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev_local.db")
SYNC_DATABASE_URL = _normalize_sync_db_url(DATABASE_URL)

print(f"[DB DEBUG] Original URL starts with: {DATABASE_URL[:16]}...")
print(f"[DB DEBUG] Final URL starts with: {SYNC_DATABASE_URL[:28]}...")
print("[DB] Using Configured Database")

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if SYNC_DATABASE_URL.startswith("sqlite://"):
    # Needed for SQLite in multi-threaded FastAPI
    connect_args = {"check_same_thread": False}

    # Critical for In-Memory usage: Maintain single connection
    if ":memory:" in SYNC_DATABASE_URL:
        engine_kwargs["poolclass"] = StaticPool
    else:
        # [HARDENING] SQLite Dialect Optimization
        # Large pools in SQLite can cause 'database is locked' under high write concurrency.
        # We use a very conservative pool for SQLite to allow multiple readers but minimize contention.
        # Postgres, however, thrives on larger pools.
        engine_kwargs["pool_size"] = 5  # Reduced from 20 for SQLite safety
        engine_kwargs["max_overflow"] = 10

else:
    # Postgres / Other: High Performance Pool
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10

engine = create_engine(SYNC_DATABASE_URL, connect_args=connect_args, **engine_kwargs)

# === WAL Mode Enablement (SQLite) ===
if SYNC_DATABASE_URL.startswith("sqlite://") and ":memory:" not in SYNC_DATABASE_URL:
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety/speed
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
