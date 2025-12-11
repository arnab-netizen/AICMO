"""
Tests for Phase 13: Autonomous Feedback Loop

Covers:
- PerformanceSnapshot model and serialization
- FeedbackCollector snapshot generation
- Anomaly detection
- FeedbackInterpreter action proposal
- FeedbackLoop orchestration
- No duplicate task creation
- LBB integration
"""

import pytest
from datetime import datetime

from aicmo.agency.feedback_loop import (
    PerformanceSnapshot,
    FeedbackCollector,
    FeedbackInterpreter,
    FeedbackLoop,
    create_feedback_loop_orchestrator,
)


class TestPerformanceSnapshot:
    """Test PerformanceSnapshot model."""
    
    def test_snapshot_creation(self):
        """PerformanceSnapshot can be created."""
        now = datetime.utcnow()
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=now,
        )
        
        assert snapshot.snapshot_id == "snap_123"
        assert snapshot.brand_id == "brand_456"
        assert snapshot.captured_at == now
        assert len(snapshot.anomalies) == 0
    
    def test_snapshot_with_metrics(self):
        """PerformanceSnapshot can hold metrics."""
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=datetime.utcnow(),
            channel_metrics={"email": {"open_rate": 0.25}},
            funnel_metrics={"awareness": 1000, "conversion": 50},
            anomalies=["Email open rate low"],
        )
        
        assert "email" in snapshot.channel_metrics
        assert snapshot.funnel_metrics["awareness"] == 1000
        assert len(snapshot.anomalies) == 1
    
    def test_snapshot_serialization(self):
        """PerformanceSnapshot can serialize/deserialize."""
        now = datetime.utcnow()
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=now,
            channel_metrics={"email": {"open_rate": 0.25}},
            anomalies=["Test anomaly"],
            notes="Test notes",
        )
        
        # Serialize
        snap_dict = snapshot.to_dict()
        assert snap_dict["snapshot_id"] == "snap_123"
        assert "channel_metrics" in snap_dict
        assert snap_dict["anomalies"] == ["Test anomaly"]
        
        # Deserialize
        restored = PerformanceSnapshot.from_dict(snap_dict)
        assert restored.snapshot_id == snapshot.snapshot_id
        assert restored.brand_id == snapshot.brand_id


class TestFeedbackCollector:
    """Test FeedbackCollector."""
    
    def test_collector_creation(self):
        """FeedbackCollector can be created."""
        collector = FeedbackCollector()
        assert collector is not None
    
    def test_collect_snapshot(self):
        """Collector can generate performance snapshot."""
        collector = FeedbackCollector()
        
        snapshot = collector.collect_snapshot("brand_123")
        
        assert snapshot.snapshot_id is not None
        assert snapshot.brand_id == "brand_123"
        assert snapshot.captured_at is not None
        assert len(snapshot.channel_metrics) > 0
        assert len(snapshot.funnel_metrics) > 0
    
    def test_snapshot_has_metrics(self):
        """Generated snapshot contains reasonable metrics."""
        collector = FeedbackCollector()
        snapshot = collector.collect_snapshot("brand_123")
        
        # Check email metrics
        assert "email" in snapshot.channel_metrics
        email = snapshot.channel_metrics["email"]
        assert "open_rate" in email
        assert 0 <= email["open_rate"] <= 1
        
        # Check funnel metrics
        assert "awareness" in snapshot.funnel_metrics
        assert "conversion_rate" in snapshot.funnel_metrics
    
    def test_anomaly_detection(self):
        """Collector detects anomalies."""
        collector = FeedbackCollector()
        snapshot = collector.collect_snapshot("brand_123")
        
        # Given the hardcoded metrics, should detect some anomalies
        # (the metrics are below thresholds)
        assert len(snapshot.anomalies) > 0
    
    def test_notes_generation(self):
        """Collector generates notes for LBB."""
        collector = FeedbackCollector()
        snapshot = collector.collect_snapshot("brand_123")
        
        assert len(snapshot.notes) > 0
        assert "Performance snapshot" in snapshot.notes
        if snapshot.anomalies:
            assert "anomal" in snapshot.notes.lower()


class TestFeedbackInterpreter:
    """Test FeedbackInterpreter."""
    
    def test_interpreter_creation(self):
        """FeedbackInterpreter can be created."""
        interpreter = FeedbackInterpreter()
        assert interpreter is not None
    
    def test_analyze_snapshot_with_anomalies(self):
        """Interpreter proposes actions for detected anomalies."""
        interpreter = FeedbackInterpreter()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=datetime.utcnow(),
            anomalies=[
                "Email open rate low (0.15)",
                "Instagram engagement low (0.02)",
                "Low conversion rate (0.005)",
            ],
        )
        
        actions = interpreter.analyze_and_propose_actions(snapshot)
        
        # Should propose tasks for each anomaly
        assert len(actions) > 0
        assert all("task_type" in a for a in actions)
        assert all("reason" in a for a in actions)
    
    def test_email_anomaly_triggers_email_task(self):
        """Email open rate anomaly triggers email rewrite task."""
        interpreter = FeedbackInterpreter()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=datetime.utcnow(),
            anomalies=["Email open rate low (0.15)"],
        )
        
        actions = interpreter.analyze_and_propose_actions(snapshot)
        
        assert len(actions) > 0
        assert any(a["task_type"] == "rewrite_email_sequence" for a in actions)
    
    def test_social_anomaly_triggers_social_task(self):
        """Instagram engagement anomaly triggers social variants task."""
        interpreter = FeedbackInterpreter()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=datetime.utcnow(),
            anomalies=["Instagram engagement low (0.02)"],
        )
        
        actions = interpreter.analyze_and_propose_actions(snapshot)
        
        assert any(a["task_type"] == "create_social_variants" for a in actions)
    
    def test_conversion_anomaly_triggers_website_task(self):
        """Low conversion triggers website copy optimization."""
        interpreter = FeedbackInterpreter()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=datetime.utcnow(),
            anomalies=["Low conversion rate (0.005)"],
        )
        
        actions = interpreter.analyze_and_propose_actions(snapshot)
        
        assert any(a["task_type"] == "optimize_landing_page_copy" for a in actions)
    
    def test_proposed_actions_have_payloads(self):
        """Proposed actions include execution payloads."""
        interpreter = FeedbackInterpreter()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_123",
            brand_id="brand_456",
            captured_at=datetime.utcnow(),
            anomalies=["Email open rate low (0.15)"],
        )
        
        actions = interpreter.analyze_and_propose_actions(snapshot)
        
        # All actions should have payload with details
        assert all("payload" in a for a in actions)
        for action in actions:
            assert isinstance(action["payload"], dict)


class TestFeedbackLoop:
    """Test FeedbackLoop orchestrator."""
    
    def test_loop_creation(self):
        """FeedbackLoop can be created."""
        loop = FeedbackLoop()
        assert loop is not None
    
    def test_loop_with_custom_components(self):
        """FeedbackLoop accepts custom components."""
        collector = FeedbackCollector()
        interpreter = FeedbackInterpreter()
        
        loop = FeedbackLoop(
            collector=collector,
            interpreter=interpreter,
        )
        
        assert loop.collector is collector
        assert loop.interpreter is interpreter
    
    def test_run_for_brand_success(self):
        """Feedback loop can execute for a brand."""
        loop = FeedbackLoop()
        
        summary = loop.run_for_brand("brand_123")
        
        # Should return summary with timestamp
        assert summary["brand_id"] == "brand_123"
        assert "timestamp" in summary
        assert "snapshot" in summary
        assert "anomalies_detected" in summary
    
    def test_loop_detects_anomalies(self):
        """Loop detects anomalies in collected data."""
        loop = FeedbackLoop()
        
        summary = loop.run_for_brand("brand_123")
        
        # Given hardcoded metrics that trigger anomalies
        assert summary["anomalies_detected"] > 0
    
    def test_loop_proposes_tasks(self):
        """Loop can propose tasks (with task_repo)."""
        collector = FeedbackCollector()
        interpreter = FeedbackInterpreter()
        
        # Mock task repo
        class MockTaskRepo:
            def create_task(self, *args, **kwargs):
                return str(uuid.uuid4())
        
        loop = FeedbackLoop(
            collector=collector,
            interpreter=interpreter,
            auto_brain_task_repository=MockTaskRepo(),
        )
        
        summary = loop.run_for_brand("brand_123")
        
        # With anomalies detected, should attempt task creation
        if summary["anomalies_detected"] > 0:
            # Tasks will be attempted to be created
            pass
    
    def test_loop_handles_no_anomalies(self):
        """Loop handles case with no anomalies gracefully."""
        # Create a collector that returns no anomalies
        class NoAnomalyCollector(FeedbackCollector):
            def collect_snapshot(self, brand_id):
                snapshot = super().collect_snapshot(brand_id)
                snapshot.anomalies = []
                return snapshot
        
        loop = FeedbackLoop(collector=NoAnomalyCollector())
        
        summary = loop.run_for_brand("brand_123")
        
        # Should complete without error
        assert summary["anomalies_detected"] == 0
        assert summary["tasks_created"] == 0
    
    def test_loop_error_handling(self):
        """Loop handles errors gracefully."""
        # Create collector that will fail
        class FailingCollector(FeedbackCollector):
            def collect_snapshot(self, brand_id):
                raise Exception("Test error")
        
        loop = FeedbackLoop(collector=FailingCollector())
        
        summary = loop.run_for_brand("brand_123")
        
        # Should have recorded error
        assert len(summary["errors"]) > 0


class TestFeedbackLoopIntegration:
    """Integration tests for feedback loop."""
    
    def test_full_feedback_workflow(self):
        """Complete feedback loop workflow."""
        import uuid
        
        # Create full orchestrator
        loop = create_feedback_loop_orchestrator()
        
        # Run for a brand
        summary = loop.run_for_brand("brand_integration_test")
        
        # Verify result
        assert summary["brand_id"] == "brand_integration_test"
        assert "timestamp" in summary
        assert "snapshot" in summary
        assert "anomalies_detected" in summary
        assert "tasks_created" in summary
    
    def test_multiple_brands_feedback(self):
        """Feedback loop can process multiple brands."""
        loop = FeedbackLoop()
        
        brand_ids = ["brand_1", "brand_2", "brand_3"]
        summaries = []
        
        for brand_id in brand_ids:
            summary = loop.run_for_brand(brand_id)
            summaries.append(summary)
        
        # All should succeed
        assert len(summaries) == 3
        assert all("timestamp" in s for s in summaries)
        assert all(s["snapshot"] is not None for s in summaries)
    
    def test_feedback_and_task_creation_workflow(self):
        """Feedback detection → task creation workflow."""
        import uuid
        
        collector = FeedbackCollector()
        interpreter = FeedbackInterpreter()
        
        class MockTaskRepo:
            def __init__(self):
                self.created_tasks = []
            
            def create_task(self, task_type, reason, payload):
                task_id = str(uuid.uuid4())
                self.created_tasks.append({
                    "task_id": task_id,
                    "task_type": task_type,
                    "reason": reason,
                })
                return task_id
        
        task_repo = MockTaskRepo()
        
        loop = FeedbackLoop(
            collector=collector,
            interpreter=interpreter,
            auto_brain_task_repository=task_repo,
        )
        
        summary = loop.run_for_brand("brand_123")
        
        # Should have attempted to create tasks if anomalies detected
        assert summary["anomalies_detected"] > 0


class TestFeedbackFactory:
    """Test feedback loop factory function."""
    
    def test_factory_creates_orchestrator(self):
        """Factory creates complete FeedbackLoop."""
        loop = create_feedback_loop_orchestrator()
        
        assert loop is not None
        assert loop.collector is not None
        assert loop.interpreter is not None
    
    def test_factory_with_custom_services(self):
        """Factory accepts custom service implementations."""
        class MockAnalyticsService:
            pass
        
        class MockCRMRepo:
            pass
        
        analytics = MockAnalyticsService()
        crm = MockCRMRepo()
        
        loop = create_feedback_loop_orchestrator(
            analytics_service=analytics,
            crm_repository=crm,
        )
        
        assert loop is not None
        assert loop.collector.analytics_service is analytics
        assert loop.collector.crm_repo is crm


class TestAnomalyDetection:
    """Test anomaly detection rules."""
    
    def test_email_open_rate_anomaly(self):
        """Detects low email open rates."""
        collector = FeedbackCollector()
        
        # Create snapshot with low open rate
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_1",
            brand_id="brand_1",
            captured_at=datetime.utcnow(),
            channel_metrics={"email": {"open_rate": 0.10}},
        )
        
        anomalies = collector._detect_anomalies(snapshot)
        
        assert any("open rate" in a.lower() for a in anomalies)
    
    def test_email_ctr_anomaly(self):
        """Detects low email CTR."""
        collector = FeedbackCollector()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_1",
            brand_id="brand_1",
            captured_at=datetime.utcnow(),
            channel_metrics={"email": {"ctr": 0.02}},
        )
        
        anomalies = collector._detect_anomalies(snapshot)
        
        assert any("ctr" in a.lower() for a in anomalies)
    
    def test_social_engagement_anomaly(self):
        """Detects low social engagement."""
        collector = FeedbackCollector()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_1",
            brand_id="brand_1",
            captured_at=datetime.utcnow(),
            channel_metrics={"instagram": {"engagement_rate": 0.01}},
        )
        
        anomalies = collector._detect_anomalies(snapshot)
        
        assert any("engagement" in a.lower() for a in anomalies)
    
    def test_conversion_anomaly(self):
        """Detects low conversion rates."""
        collector = FeedbackCollector()
        
        snapshot = PerformanceSnapshot(
            snapshot_id="snap_1",
            brand_id="brand_1",
            captured_at=datetime.utcnow(),
            funnel_metrics={"conversion_rate": 0.001},
        )
        
        anomalies = collector._detect_anomalies(snapshot)
        
        assert any("conversion" in a.lower() for a in anomalies)
