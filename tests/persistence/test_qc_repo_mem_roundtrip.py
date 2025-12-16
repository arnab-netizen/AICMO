"""
Test QC in-memory repository roundtrip.

Verifies:
- Create + retrieve
- Idempotency on draft_id (latest evaluation wins)
- Read-only safety (get methods don't mutate)
- Issue list handling
"""

import pytest
from datetime import datetime, timezone
from aicmo.qc.internal.repositories_mem import InMemoryQcRepo
from aicmo.qc.api.dtos import QcResultDTO, QcIssueDTO
from aicmo.shared.ids import DraftId, QcResultId


@pytest.fixture
def repo():
    """Fresh in-memory repository."""
    return InMemoryQcRepo()


@pytest.fixture
def sample_result_passing():
    """Sample passing QC result."""
    return QcResultDTO(
        result_id=QcResultId("qc_001"),
        draft_id=DraftId("draft_001"),
        passed=True,
        score=0.85,
        issues=[],
        evaluated_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_result_failing():
    """Sample failing QC result with issues."""
    return QcResultDTO(
        result_id=QcResultId("qc_002"),
        draft_id=DraftId("draft_002"),
        passed=False,
        score=0.50,
        issues=[
            QcIssueDTO(severity="critical", section="content", reason="Grammar errors"),
            QcIssueDTO(severity="minor", section="format", reason="Missing header"),
        ],
        evaluated_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_mem_repo_save_and_retrieve_by_draft_id(repo, sample_result_passing):
    """Test basic save and get by draft_id."""
    repo.save_result(sample_result_passing)
    
    retrieved = repo.get_result(sample_result_passing.draft_id)
    
    assert retrieved is not None
    assert retrieved.result_id == sample_result_passing.result_id
    assert retrieved.draft_id == sample_result_passing.draft_id
    assert retrieved.passed is True
    assert retrieved.score == 0.85
    assert len(retrieved.issues) == 0


def test_mem_repo_save_and_retrieve_by_result_id(repo, sample_result_passing):
    """Test retrieval by result ID."""
    repo.save_result(sample_result_passing)
    
    retrieved = repo.get_by_id(sample_result_passing.result_id)
    
    assert retrieved is not None
    assert retrieved.result_id == sample_result_passing.result_id
    assert retrieved.draft_id == sample_result_passing.draft_id


def test_mem_repo_failing_result_with_issues(repo, sample_result_failing):
    """Test that issues are persisted correctly."""
    repo.save_result(sample_result_failing)
    
    retrieved = repo.get_result(sample_result_failing.draft_id)
    
    assert retrieved is not None
    assert retrieved.passed is False
    assert retrieved.score == 0.50
    assert len(retrieved.issues) == 2
    
    # Verify issues
    assert retrieved.issues[0].severity == "critical"
    assert retrieved.issues[0].section == "content"
    assert retrieved.issues[0].reason == "Grammar errors"
    
    assert retrieved.issues[1].severity == "minor"
    assert retrieved.issues[1].section == "format"


def test_mem_repo_idempotency_same_draft_id(repo, sample_result_passing):
    """Test that re-evaluation replaces existing result (latest wins)."""
    # First evaluation
    repo.save_result(sample_result_passing)
    
    # Second evaluation for same draft (different result_id)
    updated_result = QcResultDTO(
        result_id=QcResultId("qc_003"),  # Different result_id
        draft_id=sample_result_passing.draft_id,  # Same draft_id
        passed=False,  # Changed
        score=0.60,  # Changed
        issues=[QcIssueDTO(severity="major", section="style", reason="Tone issue")],
        evaluated_at=datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )
    repo.save_result(updated_result)
    
    # Should return latest result
    retrieved = repo.get_result(sample_result_passing.draft_id)
    assert retrieved.result_id == "qc_003"
    assert retrieved.passed is False
    assert retrieved.score == 0.60
    assert len(retrieved.issues) == 1


def test_mem_repo_get_nonexistent_draft_returns_none(repo):
    """Test that querying non-existent draft returns None."""
    result = repo.get_result(DraftId("nonexistent"))
    assert result is None


def test_mem_repo_get_nonexistent_result_id_returns_none(repo):
    """Test that querying non-existent result ID returns None."""
    result = repo.get_by_id(QcResultId("nonexistent"))
    assert result is None


def test_mem_repo_read_only_safety(repo, sample_result_passing):
    """Test that get operations don't mutate repo state."""
    repo.save_result(sample_result_passing)
    
    # Get result
    retrieved1 = repo.get_result(sample_result_passing.draft_id)
    
    # Mutate retrieved object (should not affect repo)
    retrieved1.passed = False
    retrieved1.score = 0.0
    
    # Get again - should be unchanged
    retrieved2 = repo.get_result(sample_result_passing.draft_id)
    assert retrieved2.passed is True
    assert retrieved2.score == 0.85
