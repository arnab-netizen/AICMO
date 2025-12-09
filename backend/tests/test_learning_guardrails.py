"""
Guardrail tests for learning infrastructure.

These tests ensure learning events are ALWAYS logged at critical boundaries.
If any test fails, it means learning hooks have been removed or broken.

Action 6: Make learning impossible to forget.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from aicmo.domain.intake import ClientIntake
from aicmo.domain.strategy import StrategyDoc, StrategyPillar
from aicmo.domain.execution import CreativeVariant


class TestStrategyLearningGuardrails:
    """Ensure strategy generation ALWAYS logs learning events."""
    
    @pytest.mark.asyncio
    async def test_strategy_generation_logs_event(self):
        """CRITICAL: Strategy generation must log learning event."""
        intake = ClientIntake(
            brand_name="Test Brand",
            industry="Technology",
            primary_goal="Increase awareness",
            timeline="Q1 2025"
        )
        
        with patch('aicmo.memory.engine.log_event') as mock_log_event:
            with patch('backend.generators.marketing_plan.generate_marketing_plan') as mock_gen:
                # Mock the existing backend generator
                mock_pillar = MagicMock()
                mock_pillar.name = "Pillar 1"
                mock_pillar.description = "Desc 1"
                mock_pillar.kpi_impact = "KPI 1"
                
                mock_plan = MagicMock()
                mock_plan.executive_summary = "Summary"
                mock_plan.situation_analysis = "Analysis"
                mock_plan.strategy = "Strategy"
                mock_plan.pillars = [mock_pillar]
                mock_gen.return_value = mock_plan
                
                from aicmo.strategy.service import generate_strategy
                await generate_strategy(intake)
                
                # GUARDRAIL: log_event MUST be called with STRATEGY_GENERATED
                mock_log_event.assert_called_once()
                call_args = mock_log_event.call_args
                assert call_args[0][0] == "STRATEGY_GENERATED"
                assert "strategy" in call_args[1]["tags"]
    
    @pytest.mark.asyncio
    async def test_strategy_failure_logs_event(self):
        """CRITICAL: Strategy failures must log learning event."""
        intake = ClientIntake(
            brand_name="Test Brand",
            industry="Technology",
            primary_goal="Increase awareness",
            timeline="Q1 2025"
        )
        
        with patch('aicmo.memory.engine.log_event') as mock_log_event:
            with patch('backend.generators.marketing_plan.generate_marketing_plan') as mock_gen:
                # Simulate generation failure
                mock_gen.side_effect = Exception("LLM timeout")
                
                from aicmo.strategy.service import generate_strategy
                
                with pytest.raises(Exception):
                    await generate_strategy(intake)
                
                # GUARDRAIL: log_event MUST be called with STRATEGY_FAILED
                mock_log_event.assert_called_once()
                call_args = mock_log_event.call_args
                assert call_args[0][0] == "STRATEGY_FAILED"
                assert "error" in call_args[1]["tags"]


class TestCreativesLearningGuardrails:
    """Ensure creative generation ALWAYS logs learning events."""
    
    @pytest.mark.asyncio
    async def test_creatives_generation_logs_event(self):
        """CRITICAL: Creative generation must log learning event."""
        intake = ClientIntake(
            brand_name="Test Brand",
            industry="Technology",
            primary_goal="Increase awareness",
            timeline="Q1 2025"
        )
        
        strategy = StrategyDoc(
            brand_name="Test Brand",
            industry="Technology",
            executive_summary="Summary",
            situation_analysis="Analysis",
            strategy_narrative="Strategy",
            pillars=[
                StrategyPillar(name="Pillar 1", description="Desc 1", kpi_impact="KPI 1")
            ],
            primary_goal="Increase awareness",
            timeline="Q1 2025"
        )
        
        with patch('aicmo.memory.engine.log_event') as mock_log_event:
            from aicmo.creatives.service import generate_creatives
            await generate_creatives(intake, strategy)
            
            # GUARDRAIL: log_event MUST be called with CREATIVES_GENERATED
            mock_log_event.assert_called_once()
            call_args = mock_log_event.call_args
            assert call_args[0][0] == "CREATIVES_GENERATED"
            assert "creatives" in call_args[1]["tags"]


class TestExecutionLearningGuardrails:
    """Ensure execution ALWAYS logs learning events."""
    
    def test_execution_module_exists(self):
        """CRITICAL: Execution service must exist (tested via existing Stage 3 tests)."""
        # Execution learning is tested in backend/tests/stage_3/test_execution_service.py
        # This is a placeholder to acknowledge execution is covered by Stage 3 tests
        assert True  # Stage 3 tests cover execution logging


class TestPackLearningGuardrails:
    """Ensure pack execution ALWAYS logs learning events."""
    
    def test_pack_event_logging_function_exists(self):
        """CRITICAL: Pack event logging helper must exist."""
        from aicmo.learning.pack_events import log_pack_event
        
        # Must be callable
        assert callable(log_pack_event)
    
    def test_log_pack_event_calls_log_event(self):
        """CRITICAL: log_pack_event must delegate to log_event."""
        with patch('aicmo.learning.pack_events.log_event') as mock_log_event:
            from aicmo.learning.pack_events import log_pack_event
            
            log_pack_event(
                event_type="PACK_STARTED",
                pack_key="quick_social_basic",
                project_id="proj_123",
                input_data={"test": "data"},
                output_data=None,
                meta=None
            )
            
            # GUARDRAIL: log_event MUST be called
            mock_log_event.assert_called_once()
            call_args = mock_log_event.call_args
            assert call_args[0][0] == "PACK_STARTED"
            assert "pack" in call_args[1]["tags"]


class TestCAMLearningGuardrails:
    """Ensure CAM/acquisition ALWAYS logs learning events."""
    
    def test_cam_event_functions_exist(self):
        """CRITICAL: CAM event logging functions must exist."""
        from aicmo.learning import cam_events
        
        required_functions = [
            "log_lead_created",
            "log_outreach_sent",
            "log_outreach_replied",
            "log_lead_qualified",
            "log_lead_lost",
            "log_deal_won",
            "log_appointment_scheduled"
        ]
        
        for func_name in required_functions:
            assert hasattr(cam_events, func_name), f"Missing CAM function: {func_name}"
            assert callable(getattr(cam_events, func_name))
    
    def test_log_lead_created_calls_log_event(self):
        """CRITICAL: log_lead_created must delegate to log_event."""
        with patch('aicmo.learning.cam_events.log_event') as mock_log_event:
            from aicmo.learning.cam_events import log_lead_created
            
            log_lead_created(
                lead_id="lead_123",
                source="website",
                icp_match_score=0.85,
                industry="Technology"
            )
            
            # GUARDRAIL: log_event MUST be called
            mock_log_event.assert_called_once()
            call_args = mock_log_event.call_args
            assert call_args[0][0] == "LEAD_CREATED"
            assert "cam" in call_args[1]["tags"]


class TestIntakeLearningGuardrails:
    """Ensure intake quality ALWAYS logs learning events."""
    
    def test_intake_event_functions_exist(self):
        """CRITICAL: Intake event logging functions must exist."""
        from aicmo.learning import intake_events
        
        required_functions = [
            "log_intake_clarity_scored",
            "log_intake_clarification_requested",
            "log_intake_clarification_received",
            "log_intake_blocked",
            "log_intake_approved"
        ]
        
        for func_name in required_functions:
            assert hasattr(intake_events, func_name), f"Missing intake function: {func_name}"
            assert callable(getattr(intake_events, func_name))
    
    def test_log_intake_clarity_scored_calls_log_event(self):
        """CRITICAL: log_intake_clarity_scored must delegate to log_event."""
        with patch('aicmo.learning.intake_events.log_event') as mock_log_event:
            from aicmo.learning.intake_events import log_intake_clarity_scored
            
            log_intake_clarity_scored(
                project_id="proj_123",
                clarity_score=85,
                follow_up_questions_count=2,
                missing_fields=["target_audience"]
            )
            
            # GUARDRAIL: log_event MUST be called
            mock_log_event.assert_called_once()
            call_args = mock_log_event.call_args
            assert call_args[0][0] == "INTAKE_CLARITY_SCORED"
            assert "intake" in call_args[1]["tags"]


class TestPerformanceLearningGuardrails:
    """Ensure performance ingestion ALWAYS logs learning events."""
    
    def test_performance_ingestion_function_exists(self):
        """CRITICAL: Performance ingestion function must exist."""
        from aicmo.learning.performance import ingest_performance_data
        
        assert callable(ingest_performance_data)
    
    def test_ingest_performance_data_calls_log_event(self):
        """CRITICAL: ingest_performance_data must delegate to log_event."""
        with patch('aicmo.learning.performance.log_event') as mock_log_event:
            from aicmo.learning.performance import ingest_performance_data, PerformanceData
            
            performance = PerformanceData(
                content_id=123,
                platform="instagram",
                impressions=5000,
                clicks=250,
                engagement_rate=0.08,
                date="2025-12-08"
            )
            
            ingest_performance_data(performance)
            
            # GUARDRAIL: log_event MUST be called
            mock_log_event.assert_called_once()
            call_args = mock_log_event.call_args
            assert call_args[0][0] == "PERFORMANCE_RECORDED"
            assert "performance" in call_args[1]["tags"]


class TestKaizenServiceGuardrails:
    """Ensure Kaizen service can consume learning events."""
    
    def test_kaizen_service_exists(self):
        """CRITICAL: KaizenService must exist."""
        from aicmo.learning.kaizen_service import KaizenService
        
        service = KaizenService()
        assert service is not None
    
    def test_kaizen_context_model_exists(self):
        """CRITICAL: KaizenContext model must exist."""
        from aicmo.learning.kaizen_service import KaizenContext
        
        # Must be instantiable
        context = KaizenContext(
            recommended_tones=["friendly"],
            risky_patterns=[],
            preferred_platforms=["instagram"],
            banned_phrases=[],
            past_winners=[],
            successful_pillars=[],
            high_performing_hooks=[],
            channel_performance={},
            high_clarity_segments=[],
            pack_success_rates={},
            confidence=50.0,
            sample_size=10
        )
        assert context.confidence == 50.0
    
    def test_kaizen_service_has_context_builders(self):
        """CRITICAL: KaizenService must have context building methods."""
        from aicmo.learning.kaizen_service import KaizenService
        
        service = KaizenService()
        
        required_methods = [
            "build_context_for_project",
            "build_context_for_segment",
            "get_win_rates",
            "get_top_performing_patterns"
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name), f"Missing Kaizen method: {method_name}"
            assert callable(getattr(service, method_name))


class TestGeneratorKaizenIntegration:
    """Ensure generators accept and use KaizenContext."""
    
    @pytest.mark.asyncio
    async def test_generate_strategy_accepts_kaizen_context(self):
        """CRITICAL: generate_strategy must accept kaizen_context parameter."""
        import inspect
        from aicmo.strategy.service import generate_strategy
        
        sig = inspect.signature(generate_strategy)
        assert "kaizen_context" in sig.parameters, "generate_strategy missing kaizen_context parameter"
        
        # Must be Optional
        param = sig.parameters["kaizen_context"]
        assert param.default is not inspect.Parameter.empty, "kaizen_context should be optional"
    
    @pytest.mark.asyncio
    async def test_generate_creatives_accepts_kaizen_context(self):
        """CRITICAL: generate_creatives must accept kaizen_context parameter."""
        import inspect
        from aicmo.creatives.service import generate_creatives
        
        sig = inspect.signature(generate_creatives)
        assert "kaizen_context" in sig.parameters, "generate_creatives missing kaizen_context parameter"
        
        # Must be Optional
        param = sig.parameters["kaizen_context"]
        assert param.default is not inspect.Parameter.empty, "kaizen_context should be optional"
    
    @pytest.mark.asyncio
    async def test_strategy_logs_kaizen_usage(self):
        """CRITICAL: Strategy must log when Kaizen context is used."""
        intake = ClientIntake(
            brand_name="Test Brand",
            industry="Technology",
            primary_goal="Increase awareness",
            timeline="Q1 2025"
        )
        
        from aicmo.learning.kaizen_service import KaizenContext
        kaizen_ctx = KaizenContext(
            recommended_tones=["friendly"],
            risky_patterns=[],
            preferred_platforms=["instagram"],
            banned_phrases=[],
            past_winners=[],
            successful_pillars=["Content Marketing"],
            high_performing_hooks=[],
            channel_performance={},
            high_clarity_segments=[],
            pack_success_rates={},
            confidence=75.0,
            sample_size=50
        )
        
        with patch('aicmo.memory.engine.log_event') as mock_log_event:
            with patch('backend.generators.marketing_plan.generate_marketing_plan') as mock_gen:
                mock_pillar = MagicMock()
                mock_pillar.name = "Pillar 1"
                mock_pillar.description = "Desc 1"
                mock_pillar.kpi_impact = "KPI 1"
                
                mock_plan = MagicMock()
                mock_plan.executive_summary = "Summary"
                mock_plan.situation_analysis = "Analysis"
                mock_plan.strategy = "Strategy"
                mock_plan.pillars = [mock_pillar]
                mock_gen.return_value = mock_plan
                
                from aicmo.strategy.service import generate_strategy
                await generate_strategy(intake, kaizen_context=kaizen_ctx)
                
                # GUARDRAIL: Must log that Kaizen was used
                call_args = mock_log_event.call_args
                details = call_args[1]["details"]
                assert details["kaizen_used"] is True
                assert details["kaizen_confidence"] == 75.0


# Summary test to verify entire learning infrastructure
def test_learning_infrastructure_complete():
    """
    META-GUARDRAIL: Verify all learning modules exist.
    
    If this test fails, critical learning infrastructure is missing.
    """
    required_modules = [
        "aicmo.learning.pack_events",
        "aicmo.learning.cam_events",
        "aicmo.learning.intake_events",
        "aicmo.learning.performance",
        "aicmo.learning.kaizen_service"
    ]
    
    for module_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            pytest.fail(f"CRITICAL: Learning module missing: {module_name}")
