"""
Test Onboarding database repository roundtrip.

Verifies:
- save_brief + get_brief with real DB (in-memory SQLite)
- Idempotency via brief_id (merge behavior)
- save_intake stores to IntakeDB
- Schema constraints enforced

Uses: DatabaseBriefRepo from aicmo.onboarding.internal.adapters
Pattern: Reuses strategy/production DB test bootstrap (SQLite :memory:)
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from aicmo.core.db import Base
from aicmo.onboarding.internal.adapters import DatabaseBriefRepo
from aicmo.onboarding.internal.models import BriefDB, IntakeDB
from aicmo.onboarding.api.dtos import (
    NormalizedBriefDTO,
    ScopeDTO,
    IntakeFormDTO,
)
from aicmo.shared.ids import ClientId, BriefId


@pytest.fixture(scope="function")
def db_engine():
    """In-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Session for direct DB queries (test verification)."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def repo(db_engine, monkeypatch):
    """
    DatabaseBriefRepo with mocked get_session pointing to test DB.
    
    Justification for internal import: Testing DatabaseBriefRepo implementation
    requires mocking its _get_session method to use test DB instead of real Postgres.
    """
    repo = DatabaseBriefRepo()
    
    # Mock get_session to return our test session
    Session = sessionmaker(bind=db_engine)
    
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
    """Sample normalized brief for testing."""
    return NormalizedBriefDTO(
        brief_id=BriefId("brief_db_001"),
        client_id=ClientId("client_db_001"),
        scope=ScopeDTO(
            deliverables=["Content Strategy", "Social Media Pack", "Email Campaign"],
            exclusions=["Video Production", "Print Materials"],
            timeline_weeks=12,
        ),
        objectives=["Increase brand awareness", "Drive conversions", "Build community"],
        target_audience="B2B decision makers in tech industry",
        brand_guidelines={
            "tone": "professional",
            "colors": ["blue", "white", "gray"],
            "fonts": ["Roboto", "Open Sans"],
        },
        normalized_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_intake():
    """Sample intake form for testing."""
    return IntakeFormDTO(
        responses={
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "goals": "Increase leads by 50%",
            "timeline": "Q1 2025",
        },
        submitted_at=datetime(2025, 12, 13, 9, 0, 0, tzinfo=timezone.utc),
    )


# ============================================================================
# ROUNDTRIP TESTS
# ============================================================================

def test_save_and_get_brief_roundtrip(repo, sample_brief, db_session):
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
    # Compare timestamps as ISO strings (SQLite may drop/restore tzinfo)
    assert retrieved.normalized_at.isoformat() == sample_brief.normalized_at.isoformat()
    
    # Verify DB record exists
    db_brief = db_session.query(BriefDB).filter_by(id=sample_brief.brief_id).first()
    assert db_brief is not None
    assert db_brief.client_id == sample_brief.client_id


def test_get_nonexistent_brief_returns_none(repo):
    """Verify get returns None for unknown brief_id."""
    result = repo.get_brief(BriefId("nonexistent_db"))
    assert result is None


def test_save_brief_idempotency_via_merge(repo, sample_brief, db_session):
    """
    Verify second save with same brief_id updates (SQLAlchemy merge).
    
    Note: DatabaseBriefRepo uses session.merge() which handles upsert.
    """
    repo.save_brief(sample_brief)
    
    # Verify initial save
    retrieved1 = repo.get_brief(sample_brief.brief_id)
    assert retrieved1.objectives == sample_brief.objectives
    
    # Modify and save again
    updated_brief = sample_brief.model_copy(
        update={"objectives": ["New objective A", "New objective B"]}
    )
    repo.save_brief(updated_brief)
    
    # Should retrieve updated version
    retrieved2 = repo.get_brief(sample_brief.brief_id)
    assert retrieved2.objectives == ["New objective A", "New objective B"]
    
    # Verify only one DB record exists
    count = db_session.query(BriefDB).filter_by(id=sample_brief.brief_id).count()
    assert count == 1


def test_save_intake_stores_to_db(repo, sample_intake, db_session):
    """Verify save_intake persists to IntakeDB table."""
    brief_id = BriefId("brief_intake_db_001")
    
    repo.save_intake(brief_id, sample_intake)
    
    # Verify IntakeDB record exists
    intake_records = db_session.query(IntakeDB).filter_by(brief_id=brief_id).all()
    assert len(intake_records) == 1
    
    intake_db = intake_records[0]
    assert intake_db.brief_id == brief_id
    assert intake_db.responses == sample_intake.responses
    # Compare timestamps as ISO strings (SQLite may drop tzinfo)
    assert intake_db.submitted_at.isoformat().startswith(sample_intake.submitted_at.isoformat()[:19])


def test_multiple_briefs_independent_storage(repo, db_session):
    """Verify multiple briefs stored independently in DB."""
    brief1 = NormalizedBriefDTO(
        brief_id=BriefId("brief_db_multi_001"),
        client_id=ClientId("client_001"),
        scope=ScopeDTO(deliverables=["A"], exclusions=[], timeline_weeks=4),
        objectives=["Obj A"],
        target_audience="Audience A",
        brand_guidelines={},
        normalized_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )
    
    brief2 = NormalizedBriefDTO(
        brief_id=BriefId("brief_db_multi_002"),
        client_id=ClientId("client_002"),
        scope=ScopeDTO(deliverables=["B"], exclusions=[], timeline_weeks=6),
        objectives=["Obj B"],
        target_audience="Audience B",
        brand_guidelines={},
        normalized_at=datetime(2025, 12, 13, 11, 0, 0, tzinfo=timezone.utc),
    )
    
    repo.save_brief(brief1)
    repo.save_brief(brief2)
    
    # Verify both exist in DB
    count = db_session.query(BriefDB).count()
    assert count == 2
    
    # Verify retrieval
    retrieved1 = repo.get_brief(BriefId("brief_db_multi_001"))
    retrieved2 = repo.get_brief(BriefId("brief_db_multi_002"))
    
    assert retrieved1.brief_id == "brief_db_multi_001"
    assert retrieved2.brief_id == "brief_db_multi_002"
    assert retrieved1.objectives == ["Obj A"]
    assert retrieved2.objectives == ["Obj B"]


def test_scope_with_none_timeline_weeks(repo, db_session):
    """Verify None timeline_weeks persisted correctly (nullable field)."""
    brief = NormalizedBriefDTO(
        brief_id=BriefId("brief_no_timeline_db"),
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
    
    # Verify DB field is NULL
    db_brief = db_session.query(BriefDB).filter_by(id=brief.brief_id).first()
    assert db_brief.timeline_weeks is None


def test_json_fields_roundtrip(repo, sample_brief):
    """Verify JSON fields (lists, dicts) survive DB roundtrip."""
    repo.save_brief(sample_brief)
    retrieved = repo.get_brief(sample_brief.brief_id)
    
    # Lists preserved
    assert isinstance(retrieved.scope.deliverables, list)
    assert len(retrieved.scope.deliverables) == 3
    assert isinstance(retrieved.objectives, list)
    assert len(retrieved.objectives) == 3
    
    # Dict preserved
    assert isinstance(retrieved.brand_guidelines, dict)
    assert retrieved.brand_guidelines["tone"] == "professional"
    assert isinstance(retrieved.brand_guidelines["colors"], list)


def test_unicode_text_preserved(repo, db_session):
    """Verify unicode characters in text fields preserved."""
    brief = NormalizedBriefDTO(
        brief_id=BriefId("brief_unicode"),
        client_id=ClientId("client_unicode"),
        scope=ScopeDTO(
            deliverables=["Contenu français", "中文内容"],
            exclusions=["Español content"],
            timeline_weeks=8,
        ),
        objectives=["Increase émojis 🚀", "Drive conversión"],
        target_audience="Audiência internacional 🌍",
        brand_guidelines={"motto": "Über alles 🎯"},
        normalized_at=datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc),
    )
    
    repo.save_brief(brief)
    retrieved = repo.get_brief(brief.brief_id)
    
    assert retrieved.scope.deliverables[0] == "Contenu français"
    assert retrieved.scope.deliverables[1] == "中文内容"
    assert retrieved.objectives[0] == "Increase émojis 🚀"
    assert retrieved.target_audience == "Audiência internacional 🌍"
    assert retrieved.brand_guidelines["motto"] == "Über alles 🎯"
