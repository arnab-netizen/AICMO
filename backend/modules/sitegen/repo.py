from __future__ import annotations
from typing import Optional
from sqlalchemy import create_engine, update, select, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from .db_models import Base, SiteGenRun


def get_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        # For in-memory sqlite, use StaticPool so the same DB is reused across connections
        if ":memory:" in url:
            return create_engine(
                url,
                future=True,
                echo=False,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        return create_engine(
            url, future=True, echo=False, connect_args={"check_same_thread": False}
        )
    return create_engine(url, future=True, echo=False)


def create_tables_for_sqlite(engine: Engine) -> None:
    # For SQLite tests: materialize tables without Alembic
    insp = inspect(engine)
    if not insp.has_table("sitegen_runs"):
        try:
            Base.metadata.create_all(engine)
        except OperationalError as exc:
            # ignore index-exists or concurrent creation races in test environments
            msg = str(exc).lower()
            if "already exists" in msg:
                return
            raise


class SiteGenRepo:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def create_run(self, run_id: str, project_id: str) -> None:
        with self.Session.begin() as s:
            s.add(SiteGenRun(id=run_id, project_id=project_id, state="QUEUED"))

    def mark_running(self, run_id: str) -> None:
        with self.Session.begin() as s:
            s.execute(update(SiteGenRun).where(SiteGenRun.id == run_id).values(state="RUNNING"))

    def mark_done(self, run_id: str, result: dict, score: Optional[float] = None) -> None:
        with self.Session.begin() as s:
            s.execute(
                update(SiteGenRun)
                .where(SiteGenRun.id == run_id)
                .values(state="DONE", result=result, score=score)
            )

    def mark_error(self, run_id: str, msg: str) -> None:
        with self.Session.begin() as s:
            s.execute(
                update(SiteGenRun).where(SiteGenRun.id == run_id).values(state="ERROR", error=msg)
            )

    def get(self, run_id: str) -> Optional[SiteGenRun]:
        with self.Session() as s:
            return s.execute(select(SiteGenRun).where(SiteGenRun.id == run_id)).scalar_one_or_none()
