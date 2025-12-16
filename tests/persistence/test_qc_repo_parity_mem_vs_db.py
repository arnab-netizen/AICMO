"""
Test QC repository parity - InMemory vs Database.

Verifies:
- Both repos produce identical outputs for same inputs
- Idempotency semantics match
- Read-only operations behave identically

Uses canonicalization to normalize DTOs for comparison.
"""

import pytest
from datetime import datetime, timezone
from aicmo.qc.internal.repositories_mem import InMemoryQcRepo
from aicmo.qc.internal.repositories_db import DatabaseQcRepo
from aicmo.qc.api.dtos import QcResultDTO, QcIssueDTO
from aicmo.shared.ids import DraftId, QcResultId
from tests.persistence._canon import canonicalize_dict


@pytest.fixture
def mem_repo():
    """In-memory repository."""
    return InMemoryQcRepo()


@pytest.fixture
def db_repo():
    """Database repository."""
    return DatabaseQcRepo()


@pytest.fixture(autouse=True)
def clean_qc_tables():
    """Clean QC tables before/after each test."""
    from backend.db.session import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    
    def _clean():
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM qc_issues"))
            conn.execute(text("DELETE FROM qc_results"))
    
    _clean()
    yield
    _clean()


@pytest.fixture
def sample_result_passing():
    """Sample passing QC result."""
    return QcResultDTO(
        result_id=QcResultId("qc_parity_001"),
        draft_id=DraftId("draft_parity_001"),
        passed=True,
        score=0.85,
        issues=[],
        evaluated_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_result_failing():
    """Sample failing QC result with issues."""
    return QcResultDTO(
        result_id=QcResultId("qc_parity_002"),
        draft_id=DraftId("draft_parity_002"),
        passed=False,
        score=0.50,
        issues=[
            QcIssueDTO(severity="critical", section="content", reason="Grammar errors"),
            QcIssueDTO(severity="minor", section="format", reason="Missing header"),
        ],
        evaluated_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def canonicalize_qc_result(result: QcResultDTO) -> dict:
    """Convert QC result to canonical dict for comparison."""
    return canonicalize_dict({
        "result_id": result.result_id,
        "draft_id": result.draft_id,
        "passed": result.passed,
        "score": result.score,
        "issues": [
            {
                "severity": issue.severity,
                "section": issue.section,
                "reason": issue.reason,
            }
            for issue in sorted(result.issues, key=lambda i: i.severity)  # Sort for stable comparison
        ],
        "evaluated_at": result.evaluated_at,
    })


def test_parity_save_and_retrieve_passing(mem_repo, db_repo, sample_result_passing):
    """Test that mem and db repos return identical results for passing QC."""
    # Save to both repos
    mem_repo.save_result(sample_result_passing)
    db_repo.save_result(sample_result_passing)
    
    # Retrieve from both
    mem_result = mem_repo.get_result(sample_result_passing.draft_id)
    db_result = db_repo.get_result(sample_result_passing.draft_id)
    
    # Canonicalize and compare
    mem_canon = canonicalize_qc_result(mem_result)
    db_canon = canonicalize_qc_result(db_result)
    
    assert mem_canon == db_canon


def test_parity_save_and_retrieve_failing_with_issues(mem_repo, db_repo, sample_result_failing):
    """Test that mem and db repos return identical results for failing QC with issues."""
    # Save to both repos
    mem_repo.save_result(sample_result_failing)
    db_repo.save_result(sample_result_failing)
    
    # Retrieve from both
    mem_result = mem_repo.get_result(sample_result_failing.draft_id)
    db_result = db_repo.get_result(sample_result_failing.draft_id)
    
    # Canonicalize and compare
    mem_canon = canonicalize_qc_result(mem_result)
    db_canon = canonicalize_qc_result(db_result)
    
    assert mem_canon == db_canon


def test_parity_retrieve_by_result_id(mem_repo, db_repo, sample_result_passing):
    """Test that retrieval by result_id produces identical results."""
    # Save to both repos
    mem_repo.save_result(sample_result_passing)
    db_repo.save_result(sample_result_passing)
    
    # Retrieve by result_id from both
    mem_result = mem_repo.get_by_id(sample_result_passing.result_id)
    db_result = db_repo.get_by_id(sample_result_passing.result_id)
    
    # Canonicalize and compare
    mem_canon = canonicalize_qc_result(mem_result)
    db_canon = canonicalize_qc_result(db_result)
    
    assert mem_canon == db_canon


def test_parity_idempotency_latest_wins(mem_repo, db_repo, sample_result_passing):
    """Test that both repos implement same idempotency semantics (latest wins)."""
    # First save to both
    mem_repo.save_result(sample_result_passing)
    db_repo.save_result(sample_result_passing)
    
    # Updated result for same draft
    updated_result = QcResultDTO(
        result_id=QcResultId("qc_parity_003"),
        draft_id=sample_result_passing.draft_id,
        passed=False,
        score=0.60,
        issues=[QcIssueDTO(severity="major", section="style", reason="Tone issue")],
        evaluated_at=datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    # Save updated to both
    mem_repo.save_result(updated_result)
    db_repo.save_result(updated_result)
    
    # Retrieve from both
    mem_result = mem_repo.get_result(sample_result_passing.draft_id)
    db_result = db_repo.get_result(sample_result_passing.draft_id)
    
    # Both should return updated result
    mem_canon = canonicalize_qc_result(mem_result)
    db_canon = canonicalize_qc_result(db_result)
    
    assert mem_canon == db_canon
    assert mem_result.result_id == "qc_parity_003"
    assert db_result.result_id == "qc_parity_003"


def test_parity_nonexistent_returns_none(mem_repo, db_repo):
    """Test that both repos return None for non-existent drafts."""
    nonexistent_draft = DraftId("nonexistent")
    
    mem_result = mem_repo.get_result(nonexistent_draft)
    db_result = db_repo.get_result(nonexistent_draft)
    
    assert mem_result is None
    assert db_result is None
