"""
Test Strategy in-memory repository roundtrip.

Verifies:
- Create + retrieve
- Idempotency on (brief_id, version)
- Read-only safety (get methods don't mutate)
- Rollback simulation (repo behavior on error)
"""

import pytest
from datetime import datetime, timezone
from aicmo.strategy.internal.repositories_mem import InMemoryStrategyRepo
from aicmo.strategy.api.dtos import (
    StrategyDocDTO,
    KpiDTO,
    ChannelPlanDTO,
    TimelineDTO,
)
from aicmo.shared.ids import BriefId, StrategyId


@pytest.fixture
def repo():
    """Fresh in-memory repository."""
    return InMemoryStrategyRepo()


@pytest.fixture
def sample_strategy():
    """Sample strategy DTO for testing."""
    return StrategyDocDTO(
        strategy_id=StrategyId("strat_001"),
        brief_id=BriefId("brief_001"),
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


def test_mem_repo_create_and_retrieve(repo, sample_strategy):
    """Test basic save and get operations."""
    # Save strategy
    repo.save(sample_strategy)
    
    # Retrieve by ID
    retrieved = repo.get(sample_strategy.strategy_id)
    
    assert retrieved is not None
    assert retrieved.strategy_id == sample_strategy.strategy_id
    assert retrieved.brief_id == sample_strategy.brief_id
    assert retrieved.version == sample_strategy.version
    assert retrieved.executive_summary == sample_strategy.executive_summary


def test_mem_repo_idempotency_same_strategy_id(repo, sample_strategy):
    """Test that saving same strategy_id twice is idempotent."""
    # Save twice
    repo.save(sample_strategy)
    repo.save(sample_strategy)  # Should succeed (same strategy_id)
    
    # Should only have one strategy
    strategies = repo.list_by_brief(sample_strategy.brief_id)
    assert len(strategies) == 1


def test_mem_repo_idempotency_different_strategy_id_same_brief_version(repo, sample_strategy):
    """Test that (brief_id, version) uniqueness is enforced."""
    repo.save(sample_strategy)
    
    # Try to save different strategy with same (brief_id, version)
    duplicate = StrategyDocDTO(
        strategy_id=StrategyId("strat_002"),  # Different ID
        brief_id=sample_strategy.brief_id,  # Same brief
        version=sample_strategy.version,  # Same version
        kpis=sample_strategy.kpis,
        channels=sample_strategy.channels,
        timeline=sample_strategy.timeline,
        executive_summary="Different summary",
        is_approved=False,
        created_at=datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    # Should raise ValueError (simulates DB IntegrityError)
    with pytest.raises(ValueError, match="Duplicate.*brief_id, version"):
        repo.save(duplicate)


def test_mem_repo_multiple_versions_same_brief(repo):
    """Test that same brief can have multiple versions with different version numbers."""
    brief_id = BriefId("brief_001")
    
    v1 = StrategyDocDTO(
        strategy_id=StrategyId("strat_v1"),
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
        strategy_id=StrategyId("strat_v2"),
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


def test_mem_repo_get_is_read_only(repo, sample_strategy):
    """Test that get operation doesn't mutate state."""
    repo.save(sample_strategy)
    
    # Get strategy
    retrieved1 = repo.get(sample_strategy.strategy_id)
    
    # Get again - should return same object (immutable)
    retrieved2 = repo.get(sample_strategy.strategy_id)
    
    assert retrieved1 is retrieved2  # Same object reference


def test_mem_repo_list_by_brief_is_read_only(repo, sample_strategy):
    """Test that list_by_brief doesn't mutate state."""
    repo.save(sample_strategy)
    
    # List strategies
    list1 = repo.list_by_brief(sample_strategy.brief_id)
    
    # List again - should return same results
    list2 = repo.list_by_brief(sample_strategy.brief_id)
    
    assert len(list1) == len(list2)
    assert list1[0].strategy_id == list2[0].strategy_id


def test_mem_repo_list_by_brief_ordered_by_version(repo):
    """Test that list_by_brief returns strategies ordered by version."""
    brief_id = BriefId("brief_001")
    
    # Save in reverse order
    v3 = StrategyDocDTO(
        strategy_id=StrategyId("strat_v3"),
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
        strategy_id=StrategyId("strat_v1"),
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
        strategy_id=StrategyId("strat_v2"),
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
