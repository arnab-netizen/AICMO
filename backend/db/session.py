from __future__ import annotations

import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
import sqlalchemy as sa


# Small compatibility Session subclass: accept raw SQL strings in .execute()
class SafeSession(Session):
    def execute(self, statement, *args, **kwargs):
        # Coerce plain textual SQL to sqlalchemy.text() to be compatible with
        # older callsites that pass raw strings to session.execute(...).
        if isinstance(statement, (str, bytes)):
            statement = sa.text(statement)
        return super().execute(statement, *args, **kwargs)


_ENGINE: Optional[Engine] = None
_SESSION_MAKER: Optional[sessionmaker] = None


def _resolve_db_url() -> str:
    # Tests delete both; default to in-memory sqlite
    return os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "sqlite+pysqlite:///:memory:"


def get_engine() -> Engine:
    global _ENGINE, _SESSION_MAKER
    if _ENGINE is not None:
        return _ENGINE

    db_url = _resolve_db_url()
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    _ENGINE = create_engine(db_url, connect_args=connect_args, future=True)
    _SESSION_MAKER = None
    return _ENGINE


def _get_session_maker() -> sessionmaker:
    global _SESSION_MAKER
    if _SESSION_MAKER is not None:
        return _SESSION_MAKER
    _SESSION_MAKER = sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=SafeSession,
    )
    return _SESSION_MAKER


def get_db() -> Generator[Session, None, None]:
    session = _get_session_maker()()
    try:
        yield session
    finally:
        session.close()


# --- Optional async session shim for compatibility --------------------------------
try:
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
except Exception:
    create_async_engine = None  # type: ignore
    AsyncSession = None  # type: ignore
    async_sessionmaker = None  # type: ignore

_ASYNC_ENGINE = None
_ASYNC_SESSION_MAKER = None

_db_url = None
try:
    _db_url = _resolve_db_url()
except Exception:
    _db_url = None

if create_async_engine is not None and _db_url is not None:
    # Create an async engine only if the DSN already indicates an async driver
    if "+async" in _db_url or "+aiosqlite" in _db_url or "+asyncpg" in _db_url:
        try:
            _ASYNC_ENGINE = create_async_engine(_db_url, future=True, echo=False)
            _ASYNC_SESSION_MAKER = async_sessionmaker(
                _ASYNC_ENGINE, expire_on_commit=False, class_=AsyncSession
            )
        except Exception:
            _ASYNC_ENGINE = None
            _ASYNC_SESSION_MAKER = None


async def get_session():
    """Async dependency generator used by FastAPI endpoints that expect AsyncSession.

    This is a best-effort shim: it will be available when async SQLAlchemy support
    is installed and the DATABASE_URL contains an async driver. Otherwise it will
    raise at call-time to avoid import-time errors.
    """
    if _ASYNC_SESSION_MAKER is None:
        raise RuntimeError("async session factory unavailable in this environment")
    async with _ASYNC_SESSION_MAKER() as session:
        yield session
