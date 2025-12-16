"""
Test Strategy database repository roundtrip.

Verifies:
- Create + retrieve with real DB
- Idempotency on (brief_id, version) via DB constraint
- Read-only safety (get methods don't modify updated_at)
- Rollback on exception
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from aicmo.core.db import Base
from aicmo.strategy.internal.repositories_db import DatabaseStrategyRepo
from aicmo.strategy.api.dtos import (
    StrategyDocDTO,
    KpiDTO,
    ChannelPlanDTO,
    TimelineDTO,
)
from aicmo.shared.ids import BriefId, StrategyId


@pytest.fixture(scope="function")
def db_session():
    """Create in-memory SQLite DB for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def repo():
    """Fresh database repository."""
    return DatabaseStrategyRepo()


@pytest.fixture
def sample_strategy():
    """Sample strategy DTO for testing."""
    return StrategyDocDTO(
        strategy_id=StrategyId("strat_db_001"),
        brief_id=BriefId("brief_db_001"),
        version=1,
        kpis=[
            KpiDTO(name="Leads", target_value=100, unit="leads", timeframe_days=90)
        ],
        channels=[
            ChannelPlanDTO(
                channel="linkedin",
                budget_allocation_pct=50.0,
                tactics=["Posts", "Ads"]
            )
        ],
        timeline=TimelineDTO(
            milestones=[{"name": "Launch", "week": "1"}],
            duration_weeks=4
        ),
        executive_summary="Test strategy",
        is_approved=False,
        created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_db_repo_create_and_retrieve(repo, sample_strategy, db_session):
    """Test basic save and get operations with real DB."""
    # Save strategy
    repo.save(sample_strategy)
    
    # Retrieve by ID
    retrieved = repo.get(sample_strategy.strategy_id)
    
    assert retrieved is not None
    assert retrieved.strategy_id == sample_strategy.strategy_id
    assert retrieved.brief_id == sample_strategy.brief_id
    assert retrieved.version == sample_strategy.version
    assert retrieved.executive_summary == sample_strategy.executive_summary
    assert retrieved.is_approved == False


def test_db_repo_idempotency_same_strategy_id(repo, sample_strategy, db_session):
    """Test that saving same strategy_id twice is idempotent via merge."""
    # Save twice
    repo.save(sample_strategy)
    repo.save(sample_strategy)  # Should succeed (merge behavior)
    
    # Should only have one strategy
    strategies = repo.list_by_brief(sample_strategy.brief_id)
    assert len(strategies) == 1


def test_db_repo_idempotency_constraint_violation(repo, sample_strategy, db_session):
    """Test that (brief_id, version) uniqueness is enforced by DB."""
    repo.save(sample_strategy)
    
    # Try to save different strategy with same (brief_id, version)
    duplicate = StrategyDocDTO(
        strategy_id=StrategyId("strat_db_002"),  # Different ID
        brief_id=sample_strategy.brief_id,  # Same brief
        version=sample_strategy.version,  # Same version
        kpis=sample_strategy.kpis,
        channels=sample_strategy.channels,
        timeline=sample_strategy.timeline,
        executive_summary="Different summary",
        is_approved=False,
        created_at=datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    # Should raise IntegrityError (unique constraint violation)
    with pytest.raises(IntegrityError):
        repo.save(duplicate)


def test_db_repo_multiple_versions_same_brief(repo, db_session):
    """Test that same brief can have multiple versions with different version numbers."""
    brief_id = BriefId("brief_db_002")
    
    v1 = StrategyDocDTO(
        strategy_id=StrategyId("strat_db_v1"),
        brief_id=brief_id,
        version=1,
        kpis=[],
        channels=[],
        timeline=TimelineDTO(milestones=[], duration_weeks=4),
        executive_summary="Version 1",
        is_approved=False,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    
    v2 = StrategyDocDTO(
        strategy_id=StrategyId("strat_db_v2"),
        brief_id=brief_id,
        version=2,
        kpis=[],
        channels=[],
        timeline=TimelineDTO(milestones=[], duration_weeks=4),
        executive_summary="Version 2",
        is_approved=False,
        created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
    )
    
    repo.save(v1)
    repo.save(v2)
    
    strategies = repo.list_by_brief(brief_id)
    assert len(strategies) == 2
    assert strategies[0].version == 1
    assert strategies[1].version == 2


def test_db_repo_get_is_read_only(repo, sample_strategy, db_session):
    """Test that get operation doesn't modify updated_at."""
    repo.save(sample_strategy)
    
    # Get initial updated_at
    from aicmo.strategy.internal.models import StrategyDocumentDB
    with repo._get_session() as session:
        strategy_db = session.query(StrategyDocumentDB).filter_by(id=sample_strategy.strategy_id).first()
        initial_updated_at = strategy_db.updated_at
    
    # Call get (read operation)
    retrieved = repo.get(sample_strategy.strategy_id)
    
    # Check updated_at unchanged
    with repo._get_session() as session:
        strategy_db = session.query(StrategyDocumentDB).filter_by(id=sample_strategy.strategy_id).first()
        after_read_updated_at = strategy_db.updated_at
    
    assert after_read_updated_at == initial_updated_at


def test_db_repo_list_by_brief_is_read_only(repo, sample_strategy, db_session):
    """Test that list_by_brief doesn't modify updated_at."""
    repo.save(sample_strategy)
    
    # Get initial updated_at
    from aicmo.strategy.internal.models import StrategyDocumentDB
    with repo._get_session() as session:
        strategy_db = session.query(StrategyDocumentDB).filter_by(id=sample_strategy.strategy_id).first()
        initial_updated_at = strategy_db.updated_at
    
    # Call list_by_brief (read operation)
    strategies = repo.list_by_brief(sample_strategy.brief_id)
    
    # Check updated_at unchanged
    with repo._get_session() as session:
        strategy_db = session.query(StrategyDocumentDB).filter_by(id=sample_strategy.strategy_id).first()
        after_read_updated_at = strategy_db.updated_at
    
    assert after_read_updated_at == initial_updated_at


def test_db_repo_list_by_brief_ordered_by_version(repo, db_session):
    """Test that list_by_brief returns strategies ordered by version."""
    brief_id = BriefId("brief_db_003")
    
    # Save in reverse order
    v3 = StrategyDocDTO(
        strategy_id=StrategyId("strat_db_v3"),
        brief_id=brief_id,
        version=3,
        kpis=[],
        channels=[],
        timeline=TimelineDTO(milestones=[], duration_weeks=4),
        executive_summary="V3",
        is_approved=False,
        created_at=datetime(2025, 1, 3, tzinfo=timezone.utc),
    )
    v1 = StrategyDocDTO(
        strategy_id=StrategyId("strat_db_v1"),
        brief_id=brief_id,
        version=1,
        kpis=[],
        channels=[],
        timeline=TimelineDTO(milestones=[], duration_weeks=4),
        executive_summary="V1",
        is_approved=False,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    v2 = StrategyDocDTO(
        strategy_id=StrategyId("strat_db_v2"),
        brief_id=brief_id,
        version=2,
        kpis=[],
        channels=[],
        timeline=TimelineDTO(milestones=[], duration_weeks=4),
        executive_summary="V2",
        is_approved=False,
        created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
    )
    
    repo.save(v3)
    repo.save(v1)
    repo.save(v2)
    
    strategies = repo.list_by_brief(brief_id)
    assert [s.version for s in strategies] == [1, 2, 3]


def test_db_repo_rollback_on_exception(repo, sample_strategy, db_session):
    """Test that DB rollback occurs on exception."""
    # This test verifies that the context manager handles rollback
    # IntegrityError test above already proves rollback behavior
    # (duplicate insert doesn't corrupt DB state)
    
    repo.save(sample_strategy)
    
    # Verify only one strategy exists
    strategies = repo.list_by_brief(sample_strategy.brief_id)
    assert len(strategies) == 1
    
    # Try to insert duplicate (will fail and rollback)
    duplicate = StrategyDocDTO(
        strategy_id=StrategyId("strat_db_duplicate"),
        brief_id=sample_strategy.brief_id,
        version=sample_strategy.version,
        kpis=sample_strategy.kpis,
        channels=sample_strategy.channels,
        timeline=sample_strategy.timeline,
        executive_summary="Duplicate",
        is_approved=False,
        created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
    )
    
    try:
        repo.save(duplicate)
    except IntegrityError:
        pass  # Expected
    
    # Verify still only one strategy (rollback worked)
    strategies = repo.list_by_brief(sample_strategy.brief_id)
    assert len(strategies) == 1
    assert strategies[0].strategy_id == sample_strategy.strategy_id
