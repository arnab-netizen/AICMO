from __future__ import annotations
from typing import Dict, Literal, Optional
from dataclasses import dataclass, field
import time
import uuid

State = Literal["QUEUED", "RUNNING", "DONE", "ERROR", "CANCELLED"]


@dataclass
class TaskRecord:
    task_id: str
    state: State = "QUEUED"
    score: Optional[float] = None
    result: Optional[dict] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


class InMemoryStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}

    def enqueue(self, payload: dict) -> str:
        tid = f"tsk_{uuid.uuid4().hex[:10]}"
        self._tasks[tid] = TaskRecord(task_id=tid, state="QUEUED")
        return tid

    def start(self, tid: str) -> None:
        self._tasks[tid].state = "RUNNING"

    def complete(self, tid: str, result: dict, score: float | None = None) -> None:
        t = self._tasks[tid]
        t.state = "DONE"
        t.result = result
        t.score = score

    def set_error(self, tid: str, msg: str) -> None:
        t = self._tasks[tid]
        t.state = "ERROR"
        t.error = msg

    def get(self, tid: str) -> TaskRecord:
        return self._tasks[tid]


STORE = InMemoryStore()
STORE = InMemoryStore()
