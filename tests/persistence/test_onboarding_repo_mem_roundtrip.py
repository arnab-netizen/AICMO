"""
Test Onboarding in-memory repository roundtrip.

Verifies:
- save_brief + get_brief with in-memory storage
- save_intake + retrieval semantics
- Idempotency via brief_id (dict key overwrite)
- No DB dependencies

Uses: InMemoryBriefRepo from aicmo.onboarding.internal.adapters
"""

import pytest
from datetime import datetime, timezone
from aicmo.onboarding.internal.adapters import InMemoryBriefRepo
from aicmo.onboarding.api.dtos import (
    NormalizedBriefDTO,
    ScopeDTO,
    IntakeFormDTO,
)
from aicmo.shared.ids import ClientId, BriefId


@pytest.fixture
def repo():
    """Fresh in-memory repository."""
    return InMemoryBriefRepo()


@pytest.fixture
def sample_brief():
    """Sample normalized brief for testing."""
    return NormalizedBriefDTO(
        brief_id=BriefId("brief_mem_001"),
        client_id=ClientId("client_mem_001"),
        scope=ScopeDTO(
            deliverables=["Content Strategy", "Social Media Pack"],
            exclusions=["Video Production"],
            timeline_weeks=8,
        ),
        objectives=["Increase brand awareness", "Drive conversions"],
        target_audience="B2B decision makers",
        brand_guidelines={"tone": "professional", "colors": ["blue", "white"]},
        normalized_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_intake():
    """Sample intake form for testing."""
    return IntakeFormDTO(
        responses={
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "goals": "Increase leads",
        },
        submitted_at=datetime(2025, 12, 13, 9, 0, 0, tzinfo=timezone.utc),
    )


# ============================================================================
# ROUNDTRIP TESTS
# ============================================================================

def test_save_and_get_brief_roundtrip(repo, sample_brief):
    """Verify save + get preserves all DTO fields."""
    repo.save_brief(sample_brief)
    retrieved = repo.get_brief(sample_brief.brief_id)
    
    assert retrieved is not None
    assert retrieved.brief_id == sample_brief.brief_id
    assert retrieved.client_id == sample_brief.client_id
    assert retrieved.scope.deliverables == sample_brief.scope.deliverables
    assert retrieved.scope.exclusions == sample_brief.scope.exclusions
    assert retrieved.scope.timeline_weeks == sample_brief.scope.timeline_weeks
    assert retrieved.objectives == sample_brief.objectives
    assert retrieved.target_audience == sample_brief.target_audience
    assert retrieved.brand_guidelines == sample_brief.brand_guidelines
    assert retrieved.normalized_at == sample_brief.normalized_at


def test_get_nonexistent_brief_returns_none(repo):
    """Verify get returns None for unknown brief_id."""
    result = repo.get_brief(BriefId("nonexistent"))
    assert result is None


def test_save_brief_idempotency_via_brief_id(repo, sample_brief):
    """Verify second save with same brief_id updates (dict overwrite)."""
    repo.save_brief(sample_brief)
    
    # Modify and save again
    updated_brief = sample_brief.model_copy(
        update={"objectives": ["New objective 1", "New objective 2"]}
    )
    repo.save_brief(updated_brief)
    
    # Should retrieve updated version
    retrieved = repo.get_brief(sample_brief.brief_id)
    assert retrieved.objectives == ["New objective 1", "New objective 2"]


def test_save_intake_stores_form_data(repo, sample_intake):
    """Verify save_intake stores intake form (basic storage check)."""
    brief_id = BriefId("brief_intake_001")
    
    # No assertion error = storage succeeded
    repo.save_intake(brief_id, sample_intake)
    
    # InMemoryBriefRepo stores in _intake_forms dict
    assert brief_id in repo._intake_forms
    assert repo._intake_forms[brief_id] == sample_intake


def test_multiple_briefs_independent_storage(repo):
    """Verify multiple briefs stored independently."""
    brief1 = NormalizedBriefDTO(
        brief_id=BriefId("brief_001"),
        client_id=ClientId("client_001"),
        scope=ScopeDTO(deliverables=["A"], exclusions=[], timeline_weeks=4),
        objectives=["Obj A"],
        target_audience="Audience A",
        brand_guidelines={},
        normalized_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )
    
    brief2 = NormalizedBriefDTO(
        brief_id=BriefId("brief_002"),
        client_id=ClientId("client_002"),
        scope=ScopeDTO(deliverables=["B"], exclusions=[], timeline_weeks=6),
        objectives=["Obj B"],
        target_audience="Audience B",
        brand_guidelines={},
        normalized_at=datetime(2025, 12, 13, 11, 0, 0, tzinfo=timezone.utc),
    )
    
    repo.save_brief(brief1)
    repo.save_brief(brief2)
    
    retrieved1 = repo.get_brief(BriefId("brief_001"))
    retrieved2 = repo.get_brief(BriefId("brief_002"))
    
    assert retrieved1.brief_id == "brief_001"
    assert retrieved2.brief_id == "brief_002"
    assert retrieved1.objectives == ["Obj A"]
    assert retrieved2.objectives == ["Obj B"]


def test_scope_with_none_timeline_weeks(repo):
    """Verify None timeline_weeks handled correctly."""
    brief = NormalizedBriefDTO(
        brief_id=BriefId("brief_no_timeline"),
        client_id=ClientId("client_001"),
        scope=ScopeDTO(
            deliverables=["Content"],
            exclusions=[],
            timeline_weeks=None,  # Explicit None
        ),
        objectives=["Test"],
        target_audience="Test audience",
        brand_guidelines={},
        normalized_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )
    
    repo.save_brief(brief)
    retrieved = repo.get_brief(brief.brief_id)
    
    assert retrieved.scope.timeline_weeks is None
