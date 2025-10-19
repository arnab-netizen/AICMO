"""Legacy module preserved as db_mod.py after package migration.

This file is a copy of the previous top-level `backend/db.py` shim. It's
kept only for archival purposes and to make it explicit that the canonical
API is now provided by the `backend.db` package. Do not import this file
from application code; import from `backend.db` instead.
"""

from __future__ import annotations

from warnings import warn

try:
    # Re-export canonical items from the package. Import errors should bubble
    # up in real runtime environments so callers see the real problem.
    from backend.db.base import Base  # noqa: F401
    from backend.db.session import (  # noqa: F401
        engine,
        async_engine,
        async_session_factory,
        get_session,
    )
except Exception:  # pragma: no cover - best-effort shim
    # If submodules are not importable (test bootstrap scenarios), provide
    # simple placeholders to avoid import-time crashes in other modules.
    Base = None  # type: ignore
    engine = None  # type: ignore
    async_engine = None  # type: ignore
    async_session_factory = None  # type: ignore
    get_session = None  # type: ignore


def get_db():
    """Back-compat: alias returning an async session generator via `get_session`.

    Note: this returns an async generator (the project is using async sessions).
    Keep this helper for legacy callsites expecting `get_db()` as a dependency.
    """
    # If a legacy sync SessionLocal is available, yield from it as a sync
    # dependency generator (this covers many tests and legacy callsites).
    if SessionLocal is not None:

        def _gen():
            db = SessionLocal()
            # Monkey-patch execute to accept raw SQL strings like legacy code
            orig_execute = getattr(db, "execute", None)

            def _execute(stmt, *a, **kw):
                if isinstance(stmt, str):
                    if text is None:
                        raise RuntimeError("text() function unavailable for SQL coercion")
                    return orig_execute(text(stmt), *a, **kw)
                return orig_execute(stmt, *a, **kw)

            if orig_execute is not None:
                try:
                    setattr(db, "execute", _execute)
                except Exception:
                    # best-effort; continue even if monkeypatch fails
                    pass

            try:
                yield db
            finally:
                try:
                    db.close()
                except Exception:
                    pass

        return _gen()

    # Otherwise, fall back to the async session getter if present.
    if get_session is not None:
        return get_session()

    raise RuntimeError("No database session provider available")


warn(
    "backend.db is a legacy shim; prefer `backend.db.session` and `backend.db.base`.",
    DeprecationWarning,
    stacklevel=2,
)

# --- Sync compatibility helpers (legacy API) ---------------------------------
# Create a sync ENGINE and SessionLocal when possible so older modules that
# expect synchronous helpers (get_engine, ping_db, exec_sql, ENGINE, SessionLocal)
# continue to work. This mirrors the historical behavior in the repo.
try:
    from backend.core.config import settings
except Exception:
    settings = None  # type: ignore

DATABASE_URL = getattr(settings, "DB_URL", "") if settings is not None else ""

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except Exception:
    create_engine = None  # type: ignore
    text = None  # type: ignore
    sessionmaker = None  # type: ignore

ENGINE = None
SessionLocal = None

if create_engine is not None and DATABASE_URL:
    try:
        if DATABASE_URL.startswith("sqlite"):
            ENGINE = create_engine(DATABASE_URL, future=True)
        else:
            ENGINE = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
        SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False, future=True)
    except Exception:
        ENGINE = None
        SessionLocal = None


def ping_db() -> bool:
    if ENGINE is None:
        return False
    try:
        with ENGINE.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_engine():
    if ENGINE is None:
        raise RuntimeError(
            "Engine not initialized; set DATABASE_URL and ensure DB driver is installed"
        )
    return ENGINE


def exec_sql(session, sql: str, **params):
    if text is None:
        raise RuntimeError("sqlalchemy.text() not available in this environment")
    return session.execute(text(sql), params)
