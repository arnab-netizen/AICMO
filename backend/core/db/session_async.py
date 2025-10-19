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
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Async DB session unavailable: missing driver or ENGINE not initialized. Check DATABASE_URL and installed drivers."
        )
    async with AsyncSessionLocal() as s:
        yield s
