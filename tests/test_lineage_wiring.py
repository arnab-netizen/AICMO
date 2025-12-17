"""
Test end-to-end lineage wiring for Strategy/Creatives/Execution artifacts.

Ensures that:
1. Downstream artifacts always have correct source_lineage
2. Approval is refused if lineage is missing or stale
3. Lineage helpers work correctly
"""
import copy
import pytest
from aicmo.ui.persistence.artifact_store import (
    ArtifactStore,
    Artifact,
    ArtifactType,
    ArtifactStatus,
    ArtifactValidationError,
    ArtifactStateError
)


class TestLineageBuilding:
    """Test lineage helper functions"""
    
    def setup_method(self):
        """Setup test session state"""
        self.session_state = {"_artifacts": {}}
        self.store = ArtifactStore(self.session_state, mode="inmemory")
    
    def _create_and_approve_intake(self):
        """Helper: create and approve intake"""
        intake = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "client_name": "Test Client",
                "website": "https://example.com",
                "industry": "SaaS",
                "geography": "USA",
                "primary_offer": "Demo",
                "objective": "Leads"
            }
        )
        return self.store.approve_artifact(intake, approved_by="test")
    
    def test_build_source_lineage_success(self):
        """build_source_lineage returns correct lineage when upstream approved"""
        # Create and approve intake
        intake_approved = self._create_and_approve_intake()
        
        # Build lineage
        lineage, errors = self.store.build_source_lineage(
            "test-client",
            "test-engagement",
            [ArtifactType.INTAKE]
        )
        
        assert len(errors) == 0
        assert "intake" in lineage
        assert lineage["intake"]["approved_version"] == 1
        assert lineage["intake"]["approved_at"] == intake_approved.approved_at
        assert lineage["intake"]["artifact_id"] == intake_approved.artifact_id
    
    def test_build_source_lineage_missing_upstream(self):
        """build_source_lineage returns errors when required upstream not approved"""
        # No intake approved
        lineage, errors = self.store.build_source_lineage(
            "test-client",
            "test-engagement",
            [ArtifactType.INTAKE]
        )
        
        assert len(errors) == 1
        assert "intake not approved" in errors[0].lower()
        assert len(lineage) == 0
    
    def test_assert_lineage_fresh_with_current_version(self):
        """assert_lineage_fresh passes when lineage matches current approved"""
        # Create and approve intake
        intake_approved = self._create_and_approve_intake()
        
        # Build lineage
        lineage = {
            "intake": {
                "approved_version": intake_approved.version,
                "approved_at": intake_approved.approved_at,
                "artifact_id": intake_approved.artifact_id
            }
        }
        
        # Check freshness
        ok, errors = self.store.assert_lineage_fresh(
            lineage,
            "test-client",
            "test-engagement"
        )
        
        assert ok is True
        assert len(errors) == 0
    
    def test_assert_lineage_fresh_with_stale_version(self):
        """assert_lineage_fresh fails when lineage has old version"""
        # Create and approve intake v1
        intake_v1 = self._create_and_approve_intake()
        
        # Update and approve intake v2
        new_content = copy.deepcopy(intake_v1.content)
        new_content["industry"] = "FinTech"
        intake_v2_revised = self.store.update_artifact(
            intake_v1,
            content=new_content,
            increment_version=True
        )
        intake_v2_approved = self.store.approve_artifact(intake_v2_revised, approved_by="test")
        
        # Lineage pointing to v1 (stale)
        lineage = {
            "intake": {
                "approved_version": 1,
                "approved_at": intake_v1.approved_at,
                "artifact_id": intake_v1.artifact_id
            }
        }
        
        # Check freshness
        ok, errors = self.store.assert_lineage_fresh(
            lineage,
            "test-client",
            "test-engagement"
        )
        
        assert ok is False
        assert len(errors) == 1
        assert "stale" in errors[0].lower()
        assert "v1" in errors[0] and "v2" in errors[0]


class TestStrategyLineage:
    """Test Strategy artifact lineage"""
    
    def setup_method(self):
        """Setup test session state"""
        self.session_state = {"_artifacts": {}}
        self.store = ArtifactStore(self.session_state, mode="inmemory")
    
    def _create_and_approve_intake(self):
        """Helper: create and approve intake"""
        intake = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "client_name": "Test Client",
                "website": "https://example.com",
                "industry": "SaaS",
                "geography": "USA",
                "primary_offer": "Demo",
                "objective": "Leads"
            }
        )
        return self.store.approve_artifact(intake, approved_by="test")
    
    def test_strategy_created_with_intake_lineage(self):
        """Strategy artifact has intake lineage when created from approved intake"""
        # Create and approve intake
        intake_approved = self._create_and_approve_intake()
        
        # Create strategy with intake as source
        strategy = self.store.create_artifact(
            artifact_type=ArtifactType.STRATEGY,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "icp": {"segments": [{"name": "Test", "who": "VP", "where": "B2B"}]},
                "positioning": {"statement": "Test positioning"},
                "messaging": {"core_promise": "Test promise"},
                "content_pillars": [],
                "platform_plan": [],
                "cta_rules": {},
                "measurement": {}
            },
            source_artifacts=[intake_approved]
        )
        
        # Verify lineage
        assert "intake" in strategy.source_lineage
        assert strategy.source_lineage["intake"]["approved_version"] == 1
        assert strategy.source_lineage["intake"]["artifact_id"] == intake_approved.artifact_id
    
    def test_strategy_approval_refused_with_stale_lineage(self):
        """Strategy approval fails if intake lineage is stale"""
        # Create and approve intake v1
        intake_v1 = self._create_and_approve_intake()
        
        # Create strategy from intake v1
        strategy = self.store.create_artifact(
            artifact_type=ArtifactType.STRATEGY,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "icp": {"segments": [{"name": "Test", "who": "VP", "where": "B2B"}]},
                "positioning": {"statement": "Test positioning"},
                "messaging": {"core_promise": "Test promise"},
                "content_pillars": [],
                "platform_plan": [],
                "cta_rules": {},
                "measurement": {}
            },
            source_artifacts=[intake_v1]
        )
        
        # Update and approve intake v2
        new_content = copy.deepcopy(intake_v1.content)
        new_content["industry"] = "FinTech"
        intake_v2_revised = self.store.update_artifact(
            intake_v1,
            content=new_content,
            increment_version=True
        )
        intake_v2_approved = self.store.approve_artifact(intake_v2_revised, approved_by="test")
        
        # Try to approve strategy (should fail due to stale lineage)
        with pytest.raises(ArtifactValidationError) as exc_info:
            self.store.approve_artifact(strategy, approved_by="test")
        
        assert "stale" in str(exc_info.value).lower()


class TestCreativesLineage:
    """Test Creatives artifact lineage"""
    
    def setup_method(self):
        """Setup test session state"""
        self.session_state = {"_artifacts": {}}
        self.store = ArtifactStore(self.session_state, mode="inmemory")
    
    def _create_and_approve_intake(self):
        """Helper"""
        intake = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "client_name": "Test Client",
                "website": "https://example.com",
                "industry": "SaaS",
                "geography": "USA",
                "primary_offer": "Demo",
                "objective": "Leads"
            }
        )
        return self.store.approve_artifact(intake, approved_by="test")
    
    def _create_and_approve_strategy(self, intake):
        """Helper"""
        strategy = self.store.create_artifact(
            artifact_type=ArtifactType.STRATEGY,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "icp": {"segments": [{"name": "Test", "who": "VP", "where": "B2B"}]},
                "positioning": {"statement": "Test positioning"},
                "messaging": {"core_promise": "Test promise"},
                "content_pillars": [],
                "platform_plan": [],
                "cta_rules": {},
                "measurement": {}
            },
            source_artifacts=[intake]
        )
        return self.store.approve_artifact(strategy, approved_by="test")
    
    def test_creatives_has_strategy_lineage(self):
        """Creatives created from approved strategy has correct lineage"""
        # Setup
        intake_approved = self._create_and_approve_intake()
        strategy_approved = self._create_and_approve_strategy(intake_approved)
        
        # Create creatives from strategy
        creatives = self.store.create_artifact(
            artifact_type=ArtifactType.CREATIVES,
            client_id="test-client",
            engagement_id="test-engagement",
            content={"posts": ["post1", "post2"]},
            source_artifacts=[strategy_approved]
        )
        
        # Verify lineage
        assert "strategy" in creatives.source_lineage
        assert creatives.source_lineage["strategy"]["approved_version"] == 1
        assert creatives.source_lineage["strategy"]["artifact_id"] == strategy_approved.artifact_id
    
    def test_creatives_approval_refused_after_strategy_update(self):
        """Creatives approval fails when strategy gets new approved version"""
        # Setup
        intake_approved = self._create_and_approve_intake()
        strategy_v1 = self._create_and_approve_strategy(intake_approved)
        
        # Create creatives from strategy v1
        creatives = self.store.create_artifact(
            artifact_type=ArtifactType.CREATIVES,
            client_id="test-client",
            engagement_id="test-engagement",
            content={"posts": ["post1", "post2"]},
            source_artifacts=[strategy_v1]
        )
        
        # Update and approve strategy v2
        new_content = copy.deepcopy(strategy_v1.content)
        new_content["messaging"]["core_promise"] = "Updated promise v2"
        strategy_v2_revised = self.store.update_artifact(
            strategy_v1,
            content=new_content,
            increment_version=True
        )
        strategy_v2_approved = self.store.approve_artifact(strategy_v2_revised, approved_by="test")
        
        # Try to approve creatives (should fail - stale lineage)
        with pytest.raises(ArtifactValidationError) as exc_info:
            self.store.approve_artifact(creatives, approved_by="test")
        
        assert "stale" in str(exc_info.value).lower()


class TestExecutionLineage:
    """Test Execution artifact lineage"""
    
    def setup_method(self):
        """Setup test session state"""
        self.session_state = {"_artifacts": {}}
        self.store = ArtifactStore(self.session_state, mode="inmemory")
    
    def test_execution_with_strategy_and_creatives_lineage(self):
        """Execution artifact can have both strategy and creatives lineage"""
        # Create chain: intake → strategy → creatives
        intake = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "client_name": "Test Client",
                "website": "https://example.com",
                "industry": "SaaS",
                "geography": "USA",
                "primary_offer": "Demo",
                "objective": "Leads"
            }
        )
        intake_approved = self.store.approve_artifact(intake, approved_by="test")
        
        strategy = self.store.create_artifact(
            artifact_type=ArtifactType.STRATEGY,
            client_id="test-client",
            engagement_id="test-engagement",
            content={
                "icp": {"segments": [{"name": "Test", "who": "VP", "where": "B2B"}]},
                "positioning": {"statement": "Test"},
                "messaging": {"core_promise": "Test"},
                "content_pillars": [],
                "platform_plan": [],
                "cta_rules": {},
                "measurement": {}
            },
            source_artifacts=[intake_approved]
        )
        strategy_approved = self.store.approve_artifact(strategy, approved_by="test")
        
        creatives = self.store.create_artifact(
            artifact_type=ArtifactType.CREATIVES,
            client_id="test-client",
            engagement_id="test-engagement",
            content={"posts": ["post1"]},
            source_artifacts=[strategy_approved]
        )
        creatives_approved = self.store.approve_artifact(creatives, approved_by="test")
        
        # Create execution from both strategy and creatives
        execution = self.store.create_artifact(
            artifact_type=ArtifactType.EXECUTION,
            client_id="test-client",
            engagement_id="test-engagement",
            content={"schedule": []},
            source_artifacts=[strategy_approved, creatives_approved]
        )
        
        # Verify lineage
        assert "strategy" in execution.source_lineage
        assert "creatives" in execution.source_lineage
        assert execution.source_lineage["strategy"]["approved_version"] == 1
        assert execution.source_lineage["creatives"]["approved_version"] == 1
