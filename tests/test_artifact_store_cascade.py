"""
Test artifact cascade logic for stale-state detection.

Tests that upstream changes automatically flag downstream artifacts.
"""
import copy
import pytest
from aicmo.ui.persistence.artifact_store import (
    ArtifactStore,
    Artifact,
    ArtifactType,
    ArtifactStatus,
    ArtifactStateError
)


class TestCascadeLogic:
    """Test stale-state cascade when upstream changes"""
    
    def setup_method(self):
        """Setup test session state"""
        self.session_state = {"_artifacts": {}}
        self.store = ArtifactStore(self.session_state, mode="inmemory")
    
    def _create_valid_intake(self):
        """Helper: create valid intake artifact"""
        return self.store.create_artifact(
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
    
    def _create_valid_strategy(self, intake_artifact):
        """Helper: create valid strategy artifact derived from intake"""
        return self.store.create_artifact(
            artifact_type=ArtifactType.STRATEGY,
            client_id=intake_artifact.client_id,
            engagement_id=intake_artifact.engagement_id,
            content={
                "icp": {"segments": [{"name": "Test", "who": "VP", "where": "B2B"}]},
                "positioning": {"statement": "Test positioning"},
                "messaging": {"core_promise": "Test promise"},
                "content_pillars": [],
                "platform_plan": [],
                "cta_rules": {},
                "measurement": {}
            },
            source_artifacts=[intake_artifact]
        )
    
    def test_cascade_flags_strategy_when_intake_changes(self):
        """When intake approved version increments, strategy should be flagged"""
        # Create and approve intake
        intake = self._create_valid_intake()
        intake_v1 = self.store.approve_artifact(intake, approved_by="test")
        
        # Create and approve strategy based on intake v1
        strategy = self._create_valid_strategy(intake_v1)
        strategy_approved = self.store.approve_artifact(strategy, approved_by="test")
        
        assert strategy_approved.status == ArtifactStatus.APPROVED
        assert strategy_approved.source_lineage["intake"]["approved_version"] == 1
        
        # Update intake content to create revised v2
        new_content = intake_v1.content.copy()
        new_content["industry"] = "FinTech"  # Change from SaaS to FinTech
        intake_v2_revised = self.store.update_artifact(
            intake_v1,
            content=new_content,  # Changed content
            increment_version=True
        )
        
        assert intake_v2_revised.version == 2
        assert intake_v2_revised.status == ArtifactStatus.REVISED
        
        # Strategy should still be approved (draft changes don't cascade)
        strategy_after_draft = Artifact.from_dict(self.session_state.get("artifact_strategy"))
        assert strategy_after_draft.status == ArtifactStatus.APPROVED
        
        # NOW approve intake v2 - THIS triggers cascade
        intake_v2_approved = self.store.approve_artifact(intake_v2_revised, approved_by="test")
        assert intake_v2_approved.version == 2
        assert intake_v2_approved.status == ArtifactStatus.APPROVED
        
        # Strategy should now be flagged
        updated_strategy_dict = self.session_state.get("artifact_strategy")
        assert updated_strategy_dict is not None
        
        updated_strategy = Artifact.from_dict(updated_strategy_dict)
        assert updated_strategy.status == ArtifactStatus.FLAGGED_FOR_REVIEW
        assert "flagged_reason" in updated_strategy.notes
        assert "intake" in updated_strategy.notes["flagged_reason"]
        assert "approved version changed from v1 to v2" in updated_strategy.notes["flagged_reason"]
    
    def test_cascade_does_not_flag_if_no_version_change(self):
        """If update doesn't increment version, downstream stays approved"""
        # Create and approve intake
        intake = self._create_valid_intake()
        intake_v1 = self.store.approve_artifact(intake, approved_by="test")
        
        # Create and approve strategy
        strategy = self._create_valid_strategy(intake_v1)
        strategy_approved = self.store.approve_artifact(strategy, approved_by="test")
        
        # Update intake WITHOUT version increment (same content)
        intake_updated = self.store.update_artifact(
            intake_v1,
            content=intake_v1.content,  # Same content
            increment_version=False
        )
        
        assert intake_updated.version == 1  # No increment
        
        # Strategy should still be approved
        updated_strategy_dict = self.session_state.get("artifact_strategy")
        updated_strategy = Artifact.from_dict(updated_strategy_dict)
        assert updated_strategy.status == ArtifactStatus.APPROVED
    
    def test_cascade_skips_draft_artifacts(self):
        """Cascade should only flag APPROVED downstream artifacts"""
        # Create and approve intake
        intake = self._create_valid_intake()
        intake_v1 = self.store.approve_artifact(intake, approved_by="test")
        
        # Create strategy in draft (not approved)
        strategy_draft = self._create_valid_strategy(intake_v1)
        
        assert strategy_draft.status == ArtifactStatus.DRAFT
        
        # Update and approve intake v2
        new_content = intake_v1.content.copy()
        new_content["industry"] = "FinTech"
        intake_v2_revised = self.store.update_artifact(
            intake_v1,
            content=new_content,
            increment_version=True
        )
        intake_v2 = self.store.approve_artifact(intake_v2_revised, approved_by="test")
        
        # Strategy should still be draft (not flagged, since it wasn't approved)
        updated_strategy_dict = self.session_state.get("artifact_strategy")
        updated_strategy = Artifact.from_dict(updated_strategy_dict)
        assert updated_strategy.status == ArtifactStatus.DRAFT
    
    def test_multi_level_cascade(self):
        """
        Test multi-level cascade with revised drafts vs approved versions.
        
        Scenario:
        1. Create and approve Strategy v1 from Intake approved v1
        2. Create Creatives using Strategy approved v1
        3. Update Strategy to v2 as revised (NOT approved) → creatives should NOT be flagged
        4. Approve Strategy v2 → creatives SHOULD be flagged (approved version changed)
        """
        # Step 1: Create and approve intake
        intake = self._create_valid_intake()
        intake_approved = self.store.approve_artifact(intake, approved_by="test")
        assert intake_approved.version == 1
        assert intake_approved.status == ArtifactStatus.APPROVED
        
        # Step 2: Create and approve strategy based on intake v1
        strategy = self._create_valid_strategy(intake_approved)
        strategy_v1_approved = self.store.approve_artifact(strategy, approved_by="test")
        assert strategy_v1_approved.version == 1
        assert strategy_v1_approved.status == ArtifactStatus.APPROVED
        assert strategy_v1_approved.source_lineage["intake"]["approved_version"] == 1
        
        # Step 3: Create creatives based on strategy approved v1
        creatives = self.store.create_artifact(
            artifact_type=ArtifactType.CREATIVES,
            client_id=strategy_v1_approved.client_id,
            engagement_id=strategy_v1_approved.engagement_id,
            content={"posts": ["post1", "post2"]},
            source_artifacts=[strategy_v1_approved]
        )
        creatives_approved = self.store.approve_artifact(creatives, approved_by="test")
        
        assert creatives_approved.status == ArtifactStatus.APPROVED
        assert creatives_approved.source_lineage["strategy"]["approved_version"] == 1
        
        # Step 4: Update strategy to v2 as REVISED (not approved yet)
        new_strategy_content = copy.deepcopy(strategy_v1_approved.content)
        new_strategy_content["messaging"]["core_promise"] = "Updated promise v2"
        strategy_v2_revised = self.store.update_artifact(
            strategy_v1_approved,
            content=new_strategy_content,
            increment_version=True
        )
        
        assert strategy_v2_revised.version == 2
        assert strategy_v2_revised.status == ArtifactStatus.REVISED
        
        # Creatives should still be APPROVED (draft changes don't cascade)
        creatives_after_draft = Artifact.from_dict(self.session_state.get("artifact_creatives"))
        assert creatives_after_draft.status == ArtifactStatus.APPROVED
        
        # Step 5: Approve strategy v2 → THIS should trigger cascade
        strategy_v2_approved = self.store.approve_artifact(strategy_v2_revised, approved_by="test")
        assert strategy_v2_approved.version == 2
        assert strategy_v2_approved.status == ArtifactStatus.APPROVED
        
        # NOW creatives should be flagged
        creatives_after_approval = Artifact.from_dict(self.session_state.get("artifact_creatives"))
        assert creatives_after_approval.status == ArtifactStatus.FLAGGED_FOR_REVIEW
        assert "flagged_reason" in creatives_after_approval.notes
        assert "approved version changed from v1 to v2" in creatives_after_approval.notes["flagged_reason"]


class TestStatusTransitions:
    """Test strict status transition enforcement"""
    
    def setup_method(self):
        """Setup test session state"""
        self.session_state = {"_artifacts": {}}
        self.store = ArtifactStore(self.session_state, mode="inmemory")
    
    def test_draft_to_approved_allowed(self):
        """draft -> approved is allowed"""
        artifact = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test",
            engagement_id="test",
            content={
                "client_name": "Test",
                "website": "https://example.com",
                "industry": "SaaS",
                "geography": "USA",
                "primary_offer": "Demo",
                "objective": "Leads"
            }
        )
        
        assert artifact.status == ArtifactStatus.DRAFT
        
        # Should succeed
        approved = self.store.approve_artifact(artifact, approved_by="test")
        assert approved.status == ArtifactStatus.APPROVED
    
    def test_flagged_to_approved_allowed(self):
        """flagged_for_review -> approved is allowed (re-approval)"""
        # Create and approve
        artifact = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test",
            engagement_id="test",
            content={
                "client_name": "Test",
                "website": "https://example.com",
                "industry": "SaaS",
                "geography": "USA",
                "primary_offer": "Demo",
                "objective": "Leads"
            }
        )
        approved = self.store.approve_artifact(artifact, approved_by="test")
        
        # Flag it
        flagged = self.store.flag_artifact_for_review(approved, reason="test")
        assert flagged.status == ArtifactStatus.FLAGGED_FOR_REVIEW
        
        # Re-approve should work
        re_approved = self.store.approve_artifact(flagged, approved_by="test")
        assert re_approved.status == ArtifactStatus.APPROVED
    
    def test_approved_to_approved_blocked(self):
        """approved -> approved should fail (already approved)"""
        artifact = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test",
            engagement_id="test",
            content={
                "client_name": "Test",
                "website": "https://example.com",
                "industry": "SaaS",
                "geography": "USA",
                "primary_offer": "Demo",
                "objective": "Leads"
            }
        )
        approved = self.store.approve_artifact(artifact, approved_by="test")
        
        # Try to approve again - should fail
        with pytest.raises(ArtifactStateError):
            self.store.approve_artifact(approved, approved_by="test")
