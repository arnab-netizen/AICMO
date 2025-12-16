"""
Test Onboarding repository parity (in-memory vs database).

Verifies:
- InMemoryBriefRepo and DatabaseBriefRepo produce identical results
- Canonicalization normalizes timestamps/ordering for comparison
- Both implementations honor same DTO contracts

Uses:
- InMemoryBriefRepo (dict-based storage)
- DatabaseBriefRepo (SQLAlchemy ORM)
- _canon.py helpers for normalization
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from aicmo.core.db import Base
from aicmo.onboarding.internal.adapters import InMemoryBriefRepo, DatabaseBriefRepo
from aicmo.onboarding.api.dtos import (
    NormalizedBriefDTO,
    ScopeDTO,
    IntakeFormDTO,
)
from aicmo.shared.ids import ClientId, BriefId
from tests.persistence._canon import dto_to_comparable


@pytest.fixture
def mem_repo():
    """In-memory repository."""
    return InMemoryBriefRepo()


@pytest.fixture
def db_repo(monkeypatch):
    """Database repository with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    repo = DatabaseBriefRepo()
    Session = sessionmaker(bind=engine)
    
    @contextmanager
    def mock_get_session():
        session = Session()
        try:
            yield session
        finally:
            session.close()
    
    monkeypatch.setattr(repo, "_get_session", mock_get_session)
    return repo


@pytest.fixture
def sample_brief():
    """Sample brief with deterministic timestamp."""
    return NormalizedBriefDTO(
        brief_id=BriefId("brief_parity_001"),
        client_id=ClientId("client_parity_001"),
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


# ============================================================================
# PARITY TESTS (mem vs db)
# ============================================================================

def test_save_and_get_brief_parity(mem_repo, db_repo, sample_brief):
    """Verify mem and db repos return identical results after save+get."""
    # Save to both repos
    mem_repo.save_brief(sample_brief)
    db_repo.save_brief(sample_brief)
    
    # Retrieve from both
    mem_result = mem_repo.get_brief(sample_brief.brief_id)
    db_result = db_repo.get_brief(sample_brief.brief_id)
    
    # Canonicalize for comparison (normalize timestamps, ordering)
    mem_canonical = dto_to_comparable(mem_result)
    db_canonical = dto_to_comparable(db_result)
    
    # Verify parity on all DTO fields
    assert mem_canonical["brief_id"] == db_canonical["brief_id"]
    assert mem_canonical["client_id"] == db_canonical["client_id"]
    assert mem_canonical["scope"]["deliverables"] == db_canonical["scope"]["deliverables"]
    assert mem_canonical["scope"]["exclusions"] == db_canonical["scope"]["exclusions"]
    assert mem_canonical["scope"]["timeline_weeks"] == db_canonical["scope"]["timeline_weeks"]
    assert mem_canonical["objectives"] == db_canonical["objectives"]
    assert mem_canonical["target_audience"] == db_canonical["target_audience"]
    assert mem_canonical["brand_guidelines"] == db_canonical["brand_guidelines"]
    assert mem_canonical["normalized_at"] == db_canonical["normalized_at"]


def test_get_nonexistent_returns_none_parity(mem_repo, db_repo):
    """Verify both repos return None for nonexistent brief_id."""
    nonexistent_id = BriefId("nonexistent_parity")
    
    mem_result = mem_repo.get_brief(nonexistent_id)
    db_result = db_repo.get_brief(nonexistent_id)
    
    assert mem_result is None
    assert db_result is None


def test_idempotent_save_parity(mem_repo, db_repo, sample_brief):
    """Verify both repos handle idempotent saves identically."""
    # First save
    mem_repo.save_brief(sample_brief)
    db_repo.save_brief(sample_brief)
    
    # Update and save again
    updated_brief = sample_brief.model_copy(
        update={"objectives": ["New objective"]}
    )
    mem_repo.save_brief(updated_brief)
    db_repo.save_brief(updated_brief)
    
    # Retrieve updated versions
    mem_result = mem_repo.get_brief(sample_brief.brief_id)
    db_result = db_repo.get_brief(sample_brief.brief_id)
    
    # Verify both show updated objectives
    assert mem_result.objectives == ["New objective"]
    assert db_result.objectives == ["New objective"]
    
    # Canonicalize and verify full parity
    mem_canonical = dto_to_comparable(mem_result)
    db_canonical = dto_to_comparable(db_result)
    assert mem_canonical["objectives"] == db_canonical["objectives"]


def test_multiple_briefs_parity(mem_repo, db_repo):
    """Verify both repos store multiple briefs independently."""
    briefs = [
        NormalizedBriefDTO(
            brief_id=BriefId(f"brief_parity_{i}"),
            client_id=ClientId(f"client_{i}"),
            scope=ScopeDTO(
                deliverables=[f"Deliverable {i}"],
                exclusions=[],
                timeline_weeks=4 + i,
            ),
            objectives=[f"Objective {i}"],
            target_audience=f"Audience {i}",
            brand_guidelines={},
            normalized_at=datetime(2025, 12, 13, 10, i, 0, tzinfo=timezone.utc),
        )
        for i in range(3)
    ]
    
    # Save all to both repos
    for brief in briefs:
        mem_repo.save_brief(brief)
        db_repo.save_brief(brief)
    
    # Verify retrieval parity for each
    for brief in briefs:
        mem_result = mem_repo.get_brief(brief.brief_id)
        db_result = db_repo.get_brief(brief.brief_id)
        
        mem_canonical = dto_to_comparable(mem_result)
        db_canonical = dto_to_comparable(db_result)
        
        assert mem_canonical["brief_id"] == db_canonical["brief_id"]
        assert mem_canonical["objectives"] == db_canonical["objectives"]


def test_scope_none_timeline_parity(mem_repo, db_repo):
    """Verify both repos handle None timeline_weeks identically."""
    brief = NormalizedBriefDTO(
        brief_id=BriefId("brief_none_timeline"),
        client_id=ClientId("client_none"),
        scope=ScopeDTO(
            deliverables=["Content"],
            exclusions=[],
            timeline_weeks=None,
        ),
        objectives=["Test"],
        target_audience="Test audience",
        brand_guidelines={},
        normalized_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )
    
    mem_repo.save_brief(brief)
    db_repo.save_brief(brief)
    
    mem_result = mem_repo.get_brief(brief.brief_id)
    db_result = db_repo.get_brief(brief.brief_id)
    
    assert mem_result.scope.timeline_weeks is None
    assert db_result.scope.timeline_weeks is None
    
    # Verify via canonicalization
    mem_canonical = dto_to_comparable(mem_result)
    db_canonical = dto_to_comparable(db_result)
    assert mem_canonical["scope"]["timeline_weeks"] == db_canonical["scope"]["timeline_weeks"]
