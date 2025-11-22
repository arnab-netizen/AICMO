"""FastAPI router for learning endpoints."""

from __future__ import annotations

import logging
import os
import sqlite3
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aicmo.io.client_reports import AICMOOutputReport
from backend.services.learning import learn_from_report

logger = logging.getLogger("aicmo.learn")
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


@router.get("/debug/summary")
def phase_l_summary():
    """
    Phase L debug endpoint: Return memory database statistics.

    Useful for:
    - Verifying Phase L learning is working
    - Checking database path and persistence
    - Monitoring memory growth across sessions
    - Debugging "why isn't memory augmenting prompts?"

    Returns:
        {
            "db_path": "/path/to/aicmo_memory.db",
            "total_items": 42,
            "per_kind": {
                "Marketing Plan": 6,
                "Campaign Blueprint": 5,
                "Social Calendar": 8,
                ...
            }
        }
    """
    db_path = os.getenv("AICMO_MEMORY_DB", "db/aicmo_memory.db")
    info = {
        "db_path": db_path,
        "total_items": 0,
        "per_kind": {},
    }

    if not os.path.exists(db_path):
        logger.info(f"Phase L: DB not found at {db_path} (no learning yet)")
        return info

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Total count
        cur.execute("SELECT COUNT(*) FROM memory_items;")
        info["total_items"] = cur.fetchone()[0]

        # Per-kind breakdown
        cur.execute("SELECT kind, COUNT(*) FROM memory_items GROUP BY kind ORDER BY kind;")
        info["per_kind"] = {row[0]: row[1] for row in cur.fetchall()}

        logger.info(
            f"Phase L: {info['total_items']} items in memory ({len(info['per_kind'])} kinds)"
        )

        return info
    except Exception:
        logger.error("Phase L: Error reading Phase L database", exc_info=True)
        raise HTTPException(status_code=500, detail="Error reading Phase L database.")
    finally:
        try:
            conn.close()
        except Exception:
            pass


class LearnFromFilesRequest(BaseModel):
    """Request to learn from uploaded files."""

    project_id: Optional[str] = None
    files: list[dict] = []  # [{"filename": "...", "text": "..."}, ...]


class LearnFromFilesResponse(BaseModel):
    """Response after learning from files."""

    status: str
    items_learned: int


@router.post("/from-files", response_model=LearnFromFilesResponse)
def learn_from_files(payload: LearnFromFilesRequest) -> LearnFromFilesResponse:
    """
    Learn from uploaded training files (text-based).

    This endpoint accepts a set of text files (e.g., agency reports, case studies,
    training materials) and stores them as memory blocks for future reference.

    Args:
        payload: Request with project_id and list of files
                 Each file: {"filename": "name.txt", "text": "content..."}

    Returns:
        Response with count of items learned
    """
    from aicmo.memory.engine import learn_from_blocks

    project_id = payload.project_id
    file_blocks = payload.files

    if not file_blocks:
        logger.warning("learn_from_files called with no files")
        return LearnFromFilesResponse(status="ok", items_learned=0)

    # Convert files to blocks format
    blocks = []
    for file_item in file_blocks:
        filename = file_item.get("filename", "untitled")
        text = file_item.get("text", "").strip()

        if text:  # Only include non-empty files
            blocks.append(
                (
                    f"Training: {filename}",  # title
                    text,  # text
                )
            )
            logger.debug(f"learn_from_files: queued {len(text)} chars from '{filename}'")

    if not blocks:
        logger.warning("learn_from_files: no non-empty files to learn")
        return LearnFromFilesResponse(status="ok", items_learned=0)

    # Store in memory engine with error handling
    try:
        learned_count = learn_from_blocks(
            kind="training_pack",
            blocks=blocks,
            project_id=project_id,
            tags=["uploaded_training", "reference"],
        )
        logger.info(f"learn_from_files: stored {learned_count} blocks from {len(blocks)} files")
        return LearnFromFilesResponse(status="ok", items_learned=learned_count)
    except Exception as e:
        logger.error(f"learn_from_files: failed to store blocks: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to store learning blocks. Please try again later.",
        )
