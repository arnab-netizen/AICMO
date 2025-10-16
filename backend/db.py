from contextlib import contextmanager
from backend.core.config import settings

DATABASE_URL = settings.DB_URL

# Try to import SQLAlchemy and DB driver; if missing, provide safe fallbacks so the
# app can still start and health/readiness endpoints report correctly.
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except Exception:
    create_engine = None  # type: ignore
    text = None  # type: ignore
    sessionmaker = None  # type: ignore

ENGINE = None
SessionLocal = None

if create_engine is not None:
    try:
        # If DB is sqlite, don't try to use postgres drivers
        if DATABASE_URL.startswith("sqlite"):
            ENGINE = create_engine(DATABASE_URL, future=True)
        else:
            # create_engine will raise if driver missing; wrap it
            ENGINE = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                connect_args={"connect_timeout": settings.DB_CONNECT_TIMEOUT} if DATABASE_URL.startswith("postgresql") else {},
                future=True,
            )
        SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False, future=True)
    except Exception:
        ENGINE = None
        SessionLocal = None


def ping_db() -> bool:
    if ENGINE is None:
        return False
    try:
        with ENGINE.connect() as conn:
            # type: ignore[arg-type]
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@contextmanager
def get_session():
    if SessionLocal is None:
        raise RuntimeError("Database session unavailable: DB driver not installed or ENGINE not initialized")
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_engine():
    """Return the SQLAlchemy Engine or raise if not initialized.

    Useful for scripts that want to run raw SQL (migrations, seeds).
    """
    if ENGINE is None:
        raise RuntimeError("ENGINE not initialized; DB driver missing or DATABASE_URL misconfigured")
    return ENGINE
