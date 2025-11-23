"""FastAPI router for learning endpoints."""

from __future__ import annotations

import datetime
import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
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


# Helper function for ZIP endpoint
def _collect_training_files(root_dir: str) -> list[str]:
    """
    Recursively collect all training files (.txt, .md, .pdf) from a directory.

    Args:
        root_dir: Root directory to search

    Returns:
        List of absolute file paths
    """
    training_files = []
    trainable_extensions = {".txt", ".md", ".pdf"}

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if Path(file).suffix.lower() in trainable_extensions:
                training_files.append(os.path.join(root, file))

    return training_files


class LearnFromZipResponse(BaseModel):
    """Response after learning from a ZIP file."""

    status: str
    files_processed: int
    blocks_learned: int
    message: str


@router.post("/from-zip", response_model=LearnFromZipResponse)
async def learn_from_zip(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
) -> LearnFromZipResponse:
    """
    Learn from a ZIP file containing training documents.

    Extracts ZIP, collects all .txt, .md, .pdf files, archives a copy to
    data/learning/ for audit trail, and stores content in memory engine.

    Args:
        file: ZIP file to process
        project_id: Optional project identifier for organization

    Returns:
        Response with processing statistics
    """
    from aicmo.memory.engine import learn_from_blocks

    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")

    temp_dir = None
    try:
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp(prefix="aicmo_learning_")
        logger.info(f"learn_from_zip: created temp directory {temp_dir}")

        # Save and extract ZIP file
        zip_path = os.path.join(temp_dir, file.filename)
        contents = await file.read()

        with open(zip_path, "wb") as f:
            f.write(contents)

        # Validate ZIP format
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file format")

        logger.info(f"learn_from_zip: extracted ZIP to {temp_dir}")

        # Archive copy to data/learning for audit trail
        learning_dir = Path("/workspaces/AICMO/data/learning")
        learning_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = Path(file.filename).stem
        archived_zip = learning_dir / f"{basename}_{timestamp}.zip"
        shutil.copy2(zip_path, archived_zip)
        logger.info(f"learn_from_zip: archived copy to {archived_zip}")

        # Collect all training files
        training_files = _collect_training_files(temp_dir)

        if not training_files:
            logger.warning("learn_from_zip: no training files found in ZIP")
            return LearnFromZipResponse(
                status="ok",
                files_processed=0,
                blocks_learned=0,
                message="No training files (.txt, .md, .pdf) found in ZIP",
            )

        logger.info(f"learn_from_zip: found {len(training_files)} training files")

        # Convert files to blocks format
        blocks = []
        for file_path in training_files:
            try:
                # Read file content
                if file_path.endswith(".pdf"):
                    # For PDF files, include filename in learning (actual PDF parsing would require pdfplumber)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    blocks.append(
                        (
                            f"Training PDF: {rel_path}",
                            f"[PDF Document: {rel_path}]",  # Placeholder for now
                        )
                    )
                else:
                    # Text files (.txt, .md)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read().strip()

                    if text:  # Only include non-empty files
                        rel_path = os.path.relpath(file_path, temp_dir)
                        blocks.append(
                            (
                                f"Training: {rel_path}",
                                text,
                            )
                        )
                        logger.debug(f"learn_from_zip: queued {len(text)} chars from '{file_path}'")
            except Exception as e:
                logger.warning(f"learn_from_zip: failed to read {file_path}: {e}")
                continue

        if not blocks:
            logger.warning("learn_from_zip: no valid content in training files")
            return LearnFromZipResponse(
                status="ok",
                files_processed=len(training_files),
                blocks_learned=0,
                message="No valid content found in training files",
            )

        # Store in memory engine with error handling
        try:
            learned_count = learn_from_blocks(
                kind="training_pack_zip",
                blocks=blocks,
                project_id=project_id,
                tags=["uploaded_training_zip", "reference", f"source:{basename}"],
            )
            logger.info(
                f"learn_from_zip: stored {learned_count} blocks from {len(training_files)} files"
            )
            return LearnFromZipResponse(
                status="ok",
                files_processed=len(training_files),
                blocks_learned=learned_count,
                message=f"Successfully learned from {len(training_files)} files ({learned_count} blocks stored)",
            )
        except Exception as e:
            logger.error(f"learn_from_zip: failed to store blocks: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to store learning blocks. Please try again later.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"learn_from_zip: unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your ZIP file",
        )
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"learn_from_zip: cleaned up temp directory {temp_dir}")
