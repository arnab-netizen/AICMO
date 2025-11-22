"""Core memory engine for AICMO — vector-based learning from past reports."""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
from openai import OpenAI

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.getenv("AICMO_MEMORY_DB", "db/aicmo_memory.db")
DEFAULT_EMBEDDING_MODEL = os.getenv("AICMO_EMBEDDING_MODEL", "text-embedding-3-small")

USE_FAKE_EMBEDDINGS = os.getenv("AICMO_FAKE_EMBEDDINGS", "").lower() in (
    "1",
    "true",
    "yes",
)


def _get_client() -> OpenAI:
    """Lazy-load OpenAI client (only when needed)."""
    return OpenAI()


@dataclasses.dataclass
class MemoryItem:
    """
    One learned block of knowledge that AICMO can re-use later.
    """

    id: Optional[int]
    kind: str  # e.g. "report_section", "agency_sample", "operator_note"
    project_id: Optional[str]
    title: str
    text: str
    tags: List[str]
    created_at: dt.datetime


# -------------------------------------------------------------------
# Low-level DB helpers (SQLite with JSON-encoded vectors)
# -------------------------------------------------------------------


def _ensure_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create memory DB and table if they don't exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                project_id TEXT,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _get_conn(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get a connection to the memory DB, creating it if needed."""
    _ensure_db(db_path)
    return sqlite3.connect(db_path)


# -------------------------------------------------------------------
# Embeddings
# -------------------------------------------------------------------


def _fake_embed_texts(texts: Sequence[str], dim: int = 32) -> List[List[float]]:
    """
    Deterministic, offline 'fake' embeddings for dev mode.

    Uses SHA-256 hash of text to generate a fixed-length vector in [0, 1].
    This is NOT semantically meaningful like real embeddings, but:

    - It is deterministic across runs.
    - Similar texts often share hash prefix bits.
    - It allows you to test Phase L without calling OpenAI.
    """
    vectors: List[List[float]] = []
    for text in texts:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand/repeat digest to requested dimension
        raw_bytes = (h * ((dim // len(h)) + 1))[:dim]
        vec = [b / 255.0 for b in raw_bytes]
        vectors.append(vec)
    return vectors


def _embed_texts(
    texts: Sequence[str],
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> List[List[float]]:
    """
    Call OpenAI embeddings API once for a batch of texts.

    In dev or when quotas are hit, falls back to local deterministic
    fake embeddings so Phase L can still be exercised.
    """
    if not texts:
        return []

    # Dev / offline mode: never call OpenAI
    if USE_FAKE_EMBEDDINGS:
        logger.info("AICMO_MEMORY: Using fake embeddings (AICMO_FAKE_EMBEDDINGS=1).")
        return _fake_embed_texts(texts)

    try:
        client = _get_client()
        resp = client.embeddings.create(
            model=model,
            input=list(texts),
        )
        return [d.embedding for d in resp.data]
    except Exception as exc:
        logger.warning(
            "AICMO_MEMORY: Embedding call failed (%s). Falling back to fake embeddings.",
            exc,
        )
        return _fake_embed_texts(texts)


# -------------------------------------------------------------------
# Public: write API
# -------------------------------------------------------------------


def learn_from_blocks(
    kind: str,
    blocks: Sequence[Tuple[str, str]],
    project_id: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """
    Store multiple text blocks into memory.

    Args:
        kind: Type of block (e.g. "report_section", "agency_sample")
        blocks: Sequence of (title, text) tuples
        project_id: Optional project identifier
        tags: Optional list of tags for organization
        db_path: Path to SQLite database

    Returns:
        Number of blocks stored
    """
    if not blocks:
        return 0

    tags = list(tags or [])
    now = dt.datetime.utcnow().isoformat()

    titles = [b[0] for b in blocks]
    texts = [b[1] for b in blocks]

    embeddings = _embed_texts(texts)

    conn = _get_conn(db_path)
    try:
        cur = conn.cursor()
        for title, text, emb in zip(titles, texts, embeddings):
            cur.execute(
                """
                INSERT INTO memory_items (kind, project_id, title, text, tags, created_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kind,
                    project_id,
                    title,
                    text,
                    json.dumps(tags),
                    now,
                    json.dumps(emb),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    return len(blocks)


# -------------------------------------------------------------------
# Public: read API
# -------------------------------------------------------------------


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def retrieve_relevant_blocks(
    query: str,
    limit: int = 8,
    min_score: float = 0.15,
    kinds: Optional[Sequence[str]] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[MemoryItem]:
    """
    Given a query string (e.g. client brief), return the most relevant learned blocks.

    Args:
        query: Text query to find similar blocks
        limit: Maximum number of blocks to return
        min_score: Minimum cosine similarity score (0–1)
        kinds: Optional filter by block type
        db_path: Path to SQLite database

    Returns:
        List of MemoryItem objects, sorted by relevance (highest first)
    """
    if not query:
        return []

    conn = _get_conn(db_path)
    try:
        cur = conn.cursor()

        if kinds:
            placeholders = ",".join("?" for _ in kinds)
            cur.execute(
                f"SELECT id, kind, project_id, title, text, tags, created_at, embedding FROM memory_items WHERE kind IN ({placeholders})",
                list(kinds),
            )
        else:
            cur.execute(
                "SELECT id, kind, project_id, title, text, tags, created_at, embedding FROM memory_items"
            )

        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    query_vec = np.array(_embed_texts([query])[0], dtype=float)
    scored: List[Tuple[float, MemoryItem]] = []

    for row in rows:
        rid, kind, project_id, title, text, tags_json, created_at, emb_json = row
        try:
            emb = np.array(json.loads(emb_json), dtype=float)
        except Exception:
            continue

        score = _cosine_similarity(query_vec, emb)
        if score < min_score:
            continue

        item = MemoryItem(
            id=rid,
            kind=kind,
            project_id=project_id,
            title=title,
            text=text,
            tags=json.loads(tags_json),
            created_at=dt.datetime.fromisoformat(created_at),
        )
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mi for score, mi in scored[:limit]]


def format_blocks_for_prompt(
    items: Iterable[MemoryItem],
) -> str:
    """
    Produce a compact, model-friendly string with the retrieved blocks.
    """
    lines: List[str] = []
    for item in items:
        header = f"- [{item.kind}] {item.title}"
        text = item.text.strip()
        lines.append(header)
        lines.append(text)
        lines.append("")  # blank line

    if not lines:
        return ""

    return (
        "The following are past high-quality examples and patterns you must learn from and imitate where appropriate:\n\n"
        + "\n".join(lines)
    )


def augment_prompt_with_memory(
    brief_text: str,
    base_prompt: str,
    limit: int = 8,
) -> str:
    """
    High-level helper: retrieve relevant blocks and prepend them to the prompt.
    Safe to call even if memory is empty.

    Args:
        brief_text: Text representation of the client brief
        base_prompt: The original prompt to augment
        limit: Maximum number of learned blocks to include

    Returns:
        Augmented prompt with learned context prepended, or original if no matches
    """
    items = retrieve_relevant_blocks(query=brief_text, limit=limit)
    if not items:
        return base_prompt

    context = format_blocks_for_prompt(items)
    return f"{context}\n\n---\n\n{base_prompt}"
