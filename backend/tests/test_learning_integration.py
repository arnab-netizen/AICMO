"""
Stage 4: Learning integration tests.

Verifies that learning events are logged at all major boundaries:
1. Strategy generation (STRATEGY_GENERATED, STRATEGY_FAILED)
2. Creatives generation (CREATIVES_GENERATED)
3. Execution jobs (EXECUTION_ATTEMPTED)
4. State transitions (PROJECT_STATE_CHANGED)

Tests fail if hooks are removed (learning is required, not optional).
"""

import pytest
import tempfile
import os
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from aicmo.domain.intake import ClientIntake
from aicmo.domain.strategy import StrategyDoc, StrategyPillar
from aicmo.domain.project import Project, ProjectState
from aicmo.domain.execution import ContentItem
from aicmo.strategy.service import generate_strategy
from aicmo.creatives.service import generate_creatives
from aicmo.gateways.execution import queue_social_posts_for_campaign, run_execution_jobs, ExecutionService
from aicmo.gateways.echo import EchoSocialPoster
from aicmo.core.workflow import transition
from aicmo.cam.db_models import CampaignDB, ExecutionJobDB
from aicmo.memory.engine import log_event


class TestStage4LearningIntegration:
    """Stage 4: Learning hooks integration tests."""

    def setup_method(self):
        """Set up temporary memory database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.temp_db.close()
        self.original_db = os.environ.get('AICMO_MEMORY_DB')
        os.environ['AICMO_MEMORY_DB'] = self.temp_db.name
        
        # Initialize the database schema
        from aicmo.memory.engine import _ensure_db
        _ensure_db(self.temp_db.name)

    def teardown_method(self):
        """Clean up temporary database."""
        if self.original_db:
            os.environ['AICMO_MEMORY_DB'] = self.original_db
        else:
            os.environ.pop('AICMO_MEMORY_DB', None)
        
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def _get_learning_events(self, event_type: str = None):
        """Helper to query learning events from memory database."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.temp_db.name)
        if event_type:
            rows = conn.execute(
                "SELECT title, text, tags FROM memory_items WHERE kind='learning_event' AND title LIKE ?",
                (f"{event_type}%",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT title, text, tags FROM memory_items WHERE kind='learning_event'"
            ).fetchall()
        conn.close()
        
        events = []
        for title, text, tags_json in rows:
            events.append({
                'title': title,
                'text': text,
                'tags': json.loads(tags_json) if tags_json else []
            })
        return events

    @pytest.mark.asyncio
    async def test_strategy_generation_logs_event(self):
        """Strategy generation logs STRATEGY_GENERATED event."""
        from aicmo.io.client_reports import MarketingPlanView, StrategyPillar as BackendPillar
        
        intake = ClientIntake(
            brand_name="LearningTest Co",
            primary_goal="awareness",
            target_audience="developers"
        )
        
        # Mock the backend generator
        mock_plan = MarketingPlanView(
            executive_summary="This is a comprehensive marketing strategy designed to increase brand awareness and reach target developers through multiple digital channels and content initiatives.",
            situation_analysis="Analysis",
            strategy="Strategy",
            pillars=[
                BackendPillar(name="Pillar 1", description="Desc 1", kpi_impact="Impact 1")
            ]
        )
        
        with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(return_value=mock_plan)):
            strategy = await generate_strategy(intake)
        
        # Verify learning event was logged
        events = self._get_learning_events("STRATEGY_GENERATED")
        assert len(events) > 0, "No STRATEGY_GENERATED event logged"
        
        event = events[0]
        assert "LearningTest Co" in event['title']
        assert "strategy" in event['tags']
        assert "success" in event['tags']

    @pytest.mark.asyncio
    async def test_strategy_failure_logs_event(self):
        """Strategy generation failure logs STRATEGY_FAILED event."""
        intake = ClientIntake(
            brand_name="FailTest Co",
            primary_goal="awareness",
            target_audience="developers"
        )
        
        # Mock backend to raise exception
        with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(side_effect=Exception("Test error"))):
            with pytest.raises(Exception):
                await generate_strategy(intake)
        
        # Verify failure event was logged
        events = self._get_learning_events("STRATEGY_FAILED")
        assert len(events) > 0, "No STRATEGY_FAILED event logged"
        
        event = events[0]
        assert "FailTest Co" in event['title']
        assert "strategy" in event['tags']
        assert "error" in event['tags']

    @pytest.mark.asyncio
    async def test_creatives_generation_logs_event(self):
        """Creatives generation logs CREATIVES_GENERATED event."""
        intake = ClientIntake(
            brand_name="CreativeTest Co",
            primary_goal="engagement",
            target_audience="marketers"
        )
        
        strategy = StrategyDoc(
            brand_name="CreativeTest Co",
            primary_goal="engagement",
            executive_summary="Summary",
            situation_analysis="Analysis",
            strategy_narrative="Narrative",
            pillars=[
                StrategyPillar(name="Pillar 1", description="Desc", kpi_impact="Impact")
            ]
        )
        
        library = await generate_creatives(intake, strategy, platforms=["linkedin"])
        
        # Verify learning event was logged
        events = self._get_learning_events("CREATIVES_GENERATED")
        assert len(events) > 0, "No CREATIVES_GENERATED event logged"
        
        event = events[0]
        assert "creatives" in event['tags']
        assert "success" in event['tags']

    def test_execution_jobs_log_events(self):
        """Execution jobs log EXECUTION_ATTEMPTED events."""
        # Create in-memory database for execution
        engine = create_engine("sqlite:///:memory:")
        CampaignDB.__table__.create(engine, checkfirst=True)
        ExecutionJobDB.__table__.create(engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create campaign
        campaign = CampaignDB(name="Execution Learning Test", description="Test")
        session.add(campaign)
        session.commit()
        
        # Queue job
        items = [ContentItem(platform="linkedin", body_text="Test post")]
        queue_social_posts_for_campaign(campaign.id, items, session)
        session.commit()
        
        # Run jobs with echo adapter
        linkedin_echo = EchoSocialPoster(platform="linkedin")
        execution_service = ExecutionService()
        execution_service.register_gateway("linkedin", linkedin_echo)
        
        import asyncio
        asyncio.run(run_execution_jobs(campaign.id, session, execution_service))
        
        # Verify learning event was logged
        events = self._get_learning_events("EXECUTION_ATTEMPTED")
        assert len(events) > 0, "No EXECUTION_ATTEMPTED event logged"
        
        event = events[0]
        assert "execution" in event['tags']
        assert "linkedin" in event['tags']
        
        session.close()

    def test_state_transition_logs_event(self):
        """State transitions log PROJECT_STATE_CHANGED events."""
        project = Project(
            name="Test Project",
            campaign_id=42,
            state=ProjectState.STRATEGY_DRAFT
        )
        
        # Transition to approved
        project = transition(project, ProjectState.STRATEGY_APPROVED)
        
        # Verify learning event was logged
        events = self._get_learning_events("PROJECT_STATE_CHANGED")
        assert len(events) > 0, "No PROJECT_STATE_CHANGED event logged"
        
        event = events[0]
        assert "workflow" in event['tags']
        assert "state_transition" in event['tags']
        assert "STRATEGY_DRAFT" in event['tags']
        assert "STRATEGY_APPROVED" in event['tags']

    @pytest.mark.asyncio
    async def test_end_to_end_learning_scenario(self):
        """End-to-end scenario logs all learning events."""
        from aicmo.io.client_reports import MarketingPlanView, StrategyPillar as BackendPillar
        
        # 1. Generate strategy
        intake = ClientIntake(
            brand_name="E2E Test Co",
            primary_goal="growth",
            target_audience="businesses"
        )
        
        mock_plan = MarketingPlanView(
            executive_summary="This is a comprehensive end-to-end marketing strategy designed to drive growth and expand market presence through targeted initiatives and strategic channel optimization.",
            situation_analysis="Analysis",
            strategy="Strategy",
            pillars=[
                BackendPillar(name="Pillar 1", description="Desc", kpi_impact="Impact")
            ]
        )
        
        with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(return_value=mock_plan)):
            strategy = await generate_strategy(intake)
        
        # 2. Generate creatives
        library = await generate_creatives(intake, strategy, platforms=["twitter"])
        
        # 3. Transition project state
        project = Project(name="E2E Project", campaign_id=1, state=ProjectState.STRATEGY_DRAFT)
        project = transition(project, ProjectState.STRATEGY_APPROVED)
        project = transition(project, ProjectState.CREATIVE_IN_PROGRESS)
        
        # 4. Queue and execute job
        engine = create_engine("sqlite:///:memory:")
        CampaignDB.__table__.create(engine, checkfirst=True)
        ExecutionJobDB.__table__.create(engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        campaign = CampaignDB(name="E2E Campaign", description="Test")
        session.add(campaign)
        session.commit()
        
        items = [ContentItem(platform="twitter", body_text="E2E test")]
        queue_social_posts_for_campaign(campaign.id, items, session)
        session.commit()
        
        twitter_echo = EchoSocialPoster(platform="twitter")
        execution_service = ExecutionService()
        execution_service.register_gateway("twitter", twitter_echo)
        
        await run_execution_jobs(campaign.id, session, execution_service)
        
        # Verify all event types were logged
        all_events = self._get_learning_events()
        event_types = [e['title'].split()[0] for e in all_events]
        
        assert "STRATEGY_GENERATED" in event_types, "Missing STRATEGY_GENERATED event"
        assert "CREATIVES_GENERATED" in event_types, "Missing CREATIVES_GENERATED event"
        assert "PROJECT_STATE_CHANGED" in event_types, "Missing PROJECT_STATE_CHANGED event"
        assert "EXECUTION_ATTEMPTED" in event_types, "Missing EXECUTION_ATTEMPTED event"
        
        # Verify minimum event count (2 state transitions + 1 strategy + 1 creatives + 1 execution)
        assert len(all_events) >= 5, f"Expected at least 5 events, got {len(all_events)}"
        
        session.close()

    def test_log_event_direct_usage(self):
        """log_event function can be called directly."""
        log_event(
            "TEST_EVENT",
            project_id="test_project",
            details={"key": "value"},
            tags=["test", "direct"]
        )
        
        events = self._get_learning_events("TEST_EVENT")
        assert len(events) > 0, "No TEST_EVENT logged"
        
        event = events[0]
        assert "test" in event['tags']
        assert "direct" in event['tags']
        assert "key" in event['text']
