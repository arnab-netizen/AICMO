from __future__ import annotations
from typing import Optional, Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, Text, JSON, TIMESTAMP, text, Index
from backend.db.base import Base


class SiteGenRun(Base):
    __tablename__ = "sitegen_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(16), index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Any] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Any] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (Index("ix_sitegen_runs_state", "state"),)


class SiteGenEvent(Base):
    __tablename__ = "sitegen_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(32))
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[Any] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
