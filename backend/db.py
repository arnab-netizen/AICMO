"""Back-compat shim for DB utilities.

Prefer importing from the package submodules:

    from backend.db.base import Base
    from backend.db.session import get_session, engine

This module re-exports those symbols so legacy imports continue to work
while you migrate. It emits a DeprecationWarning to encourage moving to
`backend.db.session` / `backend.db.base`.
"""

from __future__ import annotations

from warnings import warn

try:
    # Re-export canonical items from the package. Import errors should bubble
    # up in real runtime environments so callers see the real problem.
    from backend.db.base import Base  # noqa: F401
    from backend.db.session import (  # noqa: F401
        get_session,
        get_engine as session_get_engine,
        get_db as session_get_db,
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
    """Back-compat: prefer delegating to the canonical session helpers.

    This shim returns a session generator. Prefer `backend.db.session.get_db`
    when available so runtime DB_URL changes are respected in tests.
    """
    # Delegate to the session package implementation when possible.
    if session_get_db is not None:
        return session_get_db()

    # Fallback: keep legacy behavior using the module-level SessionLocal.
    if SessionLocal is not None:

        def _gen():
            db = SessionLocal()
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
                    pass

            try:
                yield db
            finally:
                try:
                    db.close()
                except Exception:
                    pass

        return _gen()

    # If everything else fails, attempt to call the sync session getter
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

# Do not treat the DB engine as immutable at import time. Some tests set
# DB_URL/DATABASE_URL via monkeypatch after this module is imported. Keep
# a best-effort eager initialization but allow `get_engine()` to recreate the
# engine later if the environment changes.
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
    """Return the sync Engine; prefer the canonical session.get_engine when available."""
    # Prefer the session module's runtime-aware engine factory when present.
    try:
        if session_get_engine is not None:
            return session_get_engine()
    except Exception:
        # Fall back to legacy behavior below
        pass

    if ENGINE is None:
        raise RuntimeError(
            "Engine not initialized; set DATABASE_URL and ensure DB driver is installed"
        )
    return ENGINE


def exec_sql(session, sql: str, **params):
    if text is None:
        raise RuntimeError("sqlalchemy.text() not available in this environment")
    return session.execute(text(sql), params)
