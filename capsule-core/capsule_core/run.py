from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field

TaskState = Literal["QUEUED", "RUNNING", "DONE", "ERROR", "CANCELLED"]


class RunRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Module-specific inputs")


class RunResponse(BaseModel):
    task_id: str
    accepted: bool = True


class StatusResponse(BaseModel):
    task_id: str
    state: TaskState
    score: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
