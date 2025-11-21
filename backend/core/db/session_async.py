from typing import AsyncGenerator

try:
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        async_sessionmaker,
        AsyncSession,
    )
except Exception:
    # If SQLAlchemy async dependencies are missing, keep module importable and fail at runtime when used.
    create_async_engine = None  # type: ignore
    async_sessionmaker = None  # type: ignore
    AsyncSession = None  # type: ignore

from backend.core.config import settings

# Lazy/robust engine creation: avoid raising at import time if DB driver missing.
ENGINE = None
AsyncSessionLocal = None
if create_async_engine is not None:
    try:
        ENGINE = create_async_engine(settings.DB_URL, pool_pre_ping=True)
        AsyncSessionLocal = async_sessionmaker(ENGINE, expire_on_commit=False, class_=AsyncSession)
    except Exception:
        ENGINE = None
        AsyncSessionLocal = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is not None:
        async with AsyncSessionLocal() as s:
            yield s

    # Fallback shim: provide an async-compatible adapter around the
    # synchronous session factory when an async driver isn't available.
    # This enables tests that run against the in-process SQLite DB to
    # exercise async endpoints without requiring async DB drivers.
    import asyncio
    from contextlib import contextmanager

    try:
        # Import the sync contextmanager helper from backend.db.session
        from backend.db.session import get_session as _sync_get_session

        @contextmanager
        def _acquire_sync_session():
            with _sync_get_session() as s:
                yield s

        class _SyncSessionAdapter:
            def __init__(self, session):
                self._s = session

            async def execute(self, *args, **kwargs):
                return await asyncio.to_thread(self._s.execute, *args, **kwargs)

            async def commit(self):
                return await asyncio.to_thread(self._s.commit)

            async def rollback(self):
                return await asyncio.to_thread(self._s.rollback)

            async def close(self):
                return await asyncio.to_thread(self._s.close)

        # Acquire the sync session in a thread and yield the adapter
        cm = _acquire_sync_session()
        s = await asyncio.to_thread(cm.__enter__)
        try:
            yield _SyncSessionAdapter(s)
        finally:
            await asyncio.to_thread(cm.__exit__, None, None, None)
    except Exception:
        raise RuntimeError(
            "Async DB session unavailable and fallback shim failed. Check DATABASE_URL and installed drivers."
        )
