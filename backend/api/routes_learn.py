"""FastAPI router for learning endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from aicmo.io.client_reports import AICMOOutputReport
from backend.services.learning import learn_from_report

router = APIRouter(prefix="/api/learn", tags=["learn"])


class LearnFromReportRequest(BaseModel):
    """Request to learn from a completed report."""

    project_id: Optional[str] = None
    tags: Optional[list[str]] = None
    report: AICMOOutputReport


class LearnFromReportResponse(BaseModel):
    """Response after learning from a report."""

    stored_blocks: int


@router.post("/from-report", response_model=LearnFromReportResponse)
def api_learn_from_report(payload: LearnFromReportRequest) -> LearnFromReportResponse:
    """
    Learn from a completed AICMO report by storing its sections as memory blocks.

    This allows AICMO to later retrieve and reuse successful strategies and approaches
    from past reports when generating new content.

    Args:
        payload: Request with project_id, tags, and AICMOOutputReport

    Returns:
        Response with count of blocks stored
    """
    stored = learn_from_report(
        report=payload.report,
        project_id=payload.project_id,
        tags=payload.tags,
    )
    return LearnFromReportResponse(stored_blocks=stored)
