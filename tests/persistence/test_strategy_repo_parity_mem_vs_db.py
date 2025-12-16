"""
Test parity between in-memory and database strategy repositories.

Verifies that both implementations produce identical results for the same operations.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aicmo.core.db import Base
from aicmo.strategy.internal.repositories_mem import InMemoryStrategyRepo
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
def mem_repo():
    """Fresh in-memory repository."""
    return InMemoryStrategyRepo()


@pytest.fixture
def db_repo():
    """Fresh database repository."""
    return DatabaseStrategyRepo()


@pytest.fixture
def sample_strategy():
    """Sample strategy DTO for testing."""
    return StrategyDocDTO(
        strategy_id=StrategyId("strat_parity_001"),
        brief_id=BriefId("brief_parity_001"),
        version=1,
        kpis=[
            KpiDTO(name="Leads", target_value=100, unit="leads", timeframe_days=90),
            KpiDTO(name="Conversion", target_value=5.0, unit="percent", timeframe_days=90),
        ],
        channels=[
            ChannelPlanDTO(
                channel="linkedin",
                budget_allocation_pct=50.0,
                tactics=["Posts", "Ads"]
            ),
            ChannelPlanDTO(
                channel="email",
                budget_allocation_pct=30.0,
                tactics=["Newsletter"]
            ),
        ],
        timeline=TimelineDTO(
            milestones=[
                {"name": "Launch", "week": "1"},
                {"name": "Review", "week": "4"},
            ],
            duration_weeks=8
        ),
        executive_summary="Multi-channel B2B strategy",
        is_approved=False,
        created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_parity_save_and_retrieve(mem_repo, db_repo, sample_strategy, db_session):
    """Test that save and retrieve produce identical results."""
    # Save to both repos
    mem_repo.save(sample_strategy)
    db_repo.save(sample_strategy)
    
    # Retrieve from both
    mem_result = mem_repo.get(sample_strategy.strategy_id)
    db_result = db_repo.get(sample_strategy.strategy_id)
    
    # Compare all fields
    assert mem_result.strategy_id == db_result.strategy_id
    assert mem_result.brief_id == db_result.brief_id
    assert mem_result.version == db_result.version
    assert mem_result.executive_summary == db_result.executive_summary
    assert mem_result.is_approved == db_result.is_approved
    assert mem_result.approved_at == db_result.approved_at
    
    # Compare KPIs
    assert len(mem_result.kpis) == len(db_result.kpis)
    for mem_kpi, db_kpi in zip(mem_result.kpis, db_result.kpis):
        assert mem_kpi.name == db_kpi.name
        assert mem_kpi.target_value == db_kpi.target_value
        assert mem_kpi.unit == db_kpi.unit
        assert mem_kpi.timeframe_days == db_kpi.timeframe_days
    
    # Compare channels
    assert len(mem_result.channels) == len(db_result.channels)
    for mem_ch, db_ch in zip(mem_result.channels, db_result.channels):
        assert mem_ch.channel == db_ch.channel
        assert mem_ch.budget_allocation_pct == db_ch.budget_allocation_pct
        assert mem_ch.tactics == db_ch.tactics
    
    # Compare timeline
    assert mem_result.timeline.duration_weeks == db_result.timeline.duration_weeks
    assert mem_result.timeline.milestones == db_result.timeline.milestones


def test_parity_list_by_brief(mem_repo, db_repo, db_session):
    """Test that list_by_brief produces same ordering and content."""
    brief_id = BriefId("brief_parity_002")
    
    # Create multiple versions
    strategies = []
    for v in [1, 2, 3]:
        s = StrategyDocDTO(
            strategy_id=StrategyId(f"strat_parity_v{v}"),
            brief_id=brief_id,
            version=v,
            kpis=[],
            channels=[],
            timeline=TimelineDTO(milestones=[], duration_weeks=4),
            executive_summary=f"Version {v}",
            is_approved=False,
            created_at=datetime(2025, 1, v, tzinfo=timezone.utc),
        )
        strategies.append(s)
    
    # Save to both repos (in non-sequential order)
    for s in [strategies[2], strategies[0], strategies[1]]:
        mem_repo.save(s)
        db_repo.save(s)
    
    # List from both repos
    mem_list = mem_repo.list_by_brief(brief_id)
    db_list = db_repo.list_by_brief(brief_id)
    
    # Should have same length and order
    assert len(mem_list) == len(db_list)
    for mem_s, db_s in zip(mem_list, db_list):
        assert mem_s.strategy_id == db_s.strategy_id
        assert mem_s.version == db_s.version
        assert mem_s.executive_summary == db_s.executive_summary


def test_parity_get_nonexistent(mem_repo, db_repo, db_session):
    """Test that getting nonexistent strategy returns None in both repos."""
    nonexistent_id = StrategyId("strat_does_not_exist")
    
    mem_result = mem_repo.get(nonexistent_id)
    db_result = db_repo.get(nonexistent_id)
    
    assert mem_result is None
    assert db_result is None


def test_parity_list_by_brief_empty(mem_repo, db_repo, db_session):
    """Test that listing nonexistent brief returns empty list in both repos."""
    nonexistent_brief = BriefId("brief_does_not_exist")
    
    mem_list = mem_repo.list_by_brief(nonexistent_brief)
    db_list = db_repo.list_by_brief(nonexistent_brief)
    
    assert mem_list == []
    assert db_list == []


def test_parity_approved_strategy(mem_repo, db_repo, db_session):
    """Test that approved strategies serialize identically."""
    approved_strategy = StrategyDocDTO(
        strategy_id=StrategyId("strat_parity_approved"),
        brief_id=BriefId("brief_parity_003"),
        version=1,
        kpis=[],
        channels=[],
        timeline=TimelineDTO(milestones=[], duration_weeks=4),
        executive_summary="Approved strategy",
        is_approved=True,
        approved_at=datetime(2025, 1, 5, 14, 30, 0, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    mem_repo.save(approved_strategy)
    db_repo.save(approved_strategy)
    
    mem_result = mem_repo.get(approved_strategy.strategy_id)
    db_result = db_repo.get(approved_strategy.strategy_id)
    
    assert mem_result.is_approved == db_result.is_approved == True
    assert mem_result.approved_at == db_result.approved_at
