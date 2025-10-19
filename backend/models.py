from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, TIMESTAMP, JSON as _SQLJSON
from sqlalchemy.sql import func
from sqlalchemy.types import (
    DateTime,
    String as SAString,
    Integer as SAInteger,
    Float,
    Numeric,
    Text,
    TypeDecorator,
)
from decimal import Decimal
from datetime import datetime
from typing import Optional

try:
    # Prefer explicit base from backend.db.base when available
    from backend.db.base import Base  # type: ignore
except Exception:
    # Fallback: define a local DeclarativeBase so imports don't fail during
    # bootstrapping or when backend.db (module) shadows the backend.db package.
    class Base(DeclarativeBase):
        """Local fallback DeclarativeBase used when real base cannot be imported."""

        pass


class Site(Base):
    __tablename__ = "site"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


# --- Asset model (migrated to typed SQLAlchemy 2.0 pattern) ---

try:
    # optional import for pgvector; keep model workable if package missing
    from pgvector.sqlalchemy import Vector  # type: ignore[import]
except Exception:
    Vector = None

try:
    from sqlalchemy.dialects.postgresql import JSONB  # type: ignore
except Exception:  # pragma: no cover - optional import
    JSONB = None


# Use a dialect-aware TypeDecorator so the underlying SQL type is chosen at
# DDL/compile time based on the target dialect. This avoids rendering
# Postgres-specific types like VECTOR(...) into SQLite DDL when tests run
# against SQLite. If pgvector is available and the dialect is postgresql,
# the Vector type will be used; otherwise fall back to Text.


class EmbeddingType(TypeDecorator):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        # Use pgvector.Vector when the target dialect is Postgres and the
        # package is importable. Otherwise use generic Text which compiles
        # cleanly for SQLite and other dialects used in tests.
        if Vector is not None and getattr(dialect, "name", "") == "postgresql":
            # Vector is a SQLAlchemy type; wrap with dialect.type_descriptor so
            # SQLAlchemy compiles it correctly for Postgres. Use explicit dim kwarg
            # to avoid ambiguity in some Vector versions.
            return dialect.type_descriptor(Vector(dim=1536))  # type: ignore[name-defined]
        return dialect.type_descriptor(Text())


# The mapped column for embeddings uses the dialect-aware type above.
_embedding_col = mapped_column(EmbeddingType(), nullable=True)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(SAInteger, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(SAString(255), nullable=True)

    # Taste-awareness fields (use Decimal to match Numeric SQL type)
    taste_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    emotion_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    tone: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_alignment: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)

    # Keep a general score field as well (optional float)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Use JSONB on Postgres when available, else fall back to generic JSON for SQLite
    # Use the generic JSON type so SQLite tests can create tables. Using
    # Postgres-specific JSONB can break SQLite DDL in unit tests if the
    # JSONB type is importable in the environment. Use SQLAlchemy's generic
    # JSON which maps to native JSON/JSONB in Postgres and compiles for SQLite.
    _JSON_TYPE = _SQLJSON

    meta: Mapped[Optional[dict]] = mapped_column(_JSON_TYPE, nullable=True)

    embedding = _embedding_col

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
