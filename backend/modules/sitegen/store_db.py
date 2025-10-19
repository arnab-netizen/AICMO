from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
import uuid

from sqlalchemy.engine import Engine
from .repo import SiteGenRepo
from .db_models import SiteGenRun

State = Literal["QUEUED", "RUNNING", "DONE", "ERROR", "CANCELLED"]


@dataclass
class TaskRecord:
    task_id: str
    state: State
    score: Optional[float]
    result: Optional[dict]
    error: Optional[str]


class DBStore:
    """DB-backed store with the same outward interface as the in-memory store."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.repo = SiteGenRepo(engine)

    def _new_id(self) -> str:
        return f"tsk_{uuid.uuid4().hex[:10]}"

    def enqueue(self, payload: dict) -> str:
        project_id = str(payload.get("project_id", ""))
        tid = self._new_id()
        self.repo.create_run(tid, project_id)
        return tid

    def start(self, tid: str) -> None:
        self.repo.mark_running(tid)

    def complete(self, tid: str, result: dict, score: float | None = None) -> None:
        self.repo.mark_done(tid, result=result, score=score)

    def set_error(self, tid: str, msg: str) -> None:
        self.repo.mark_error(tid, msg)

    def get(self, tid: str) -> TaskRecord:
        row: SiteGenRun | None = self.repo.get(tid)
        if not row:
            raise KeyError(tid)
        return TaskRecord(
            task_id=row.id,
            state=row.state,  # type: ignore
            score=row.score,
            result=row.result,
            error=row.error,
        )
