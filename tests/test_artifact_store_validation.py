"""
Test artifact store validation enforcement.

Tests that validation is enforced at approval time and validation errors block approval.
"""
import pytest
from aicmo.ui.persistence.artifact_store import (
    ArtifactStore,
    Artifact,
    ArtifactType,
    ArtifactStatus,
    ArtifactValidationError,
    validate_intake_content,
    validate_strategy_contract
)


class TestIntakeValidation:
    """Test intake validation logic"""
    
    def test_validate_intake_missing_required_fields(self):
        """Validation should fail when required fields are missing"""
        content = {
            "client_name": "Test Client",
            # Missing: website, industry, geography, primary_offer, objective
        }
        
        ok, errors, warnings = validate_intake_content(content)
        
        assert not ok
        assert len(errors) == 5  # 5 missing required fields
        assert any("website" in err for err in errors)
        assert any("industry" in err for err in errors)
        assert any("geography" in err for err in errors)
        assert any("primary_offer" in err for err in errors)
        assert any("objective" in err for err in errors)
    
    def test_validate_intake_all_required_present(self):
        """Validation should pass when all required fields present"""
        content = {
            "client_name": "Test Client",
            "website": "https://example.com",
            "industry": "SaaS",
            "geography": "USA",
            "primary_offer": "Product Demo",
            "objective": "Leads"
        }
        
        ok, errors, warnings = validate_intake_content(content)
        
        assert ok
        assert len(errors) == 0
    
    def test_validate_intake_consistency_warnings(self):
        """Validation should generate warnings for inconsistencies"""
        content = {
            "client_name": "Test Client",
            "website": "https://example.com",
            "industry": "Education",
            "geography": "USA",
            "primary_offer": "Online Course",
            "objective": "Leads",
            "target_audience": "college students",
            "budget_range": "$10k-$50k high-ticket"
        }
        
        ok, errors, warnings = validate_intake_content(content)
        
        assert ok  # No errors, only warnings
        assert len(warnings) > 0
        # Should warn about student + high-ticket contradiction
        assert any("student" in warn.lower() and "high-ticket" in warn.lower() for warn in warnings)


class TestStrategyValidation:
    """Test strategy contract validation"""
    
    def test_validate_strategy_missing_required_fields(self):
        """Strategy validation should fail when contract fields missing"""
        content = {
            "icp": {"segments": []},
            # Missing: positioning, messaging, etc.
        }
        
        ok, errors, warnings = validate_strategy_contract(content)
        
        assert not ok
        assert len(errors) >= 3  # At minimum: positioning, messaging, content_pillars
    
    def test_validate_strategy_complete_contract(self):
        """Strategy validation should pass with complete contract"""
        content = {
            "icp": {
                "segments": [
                    {
                        "name": "Enterprise Buyers",
                        "who": "VP of Marketing",
                        "where": "B2B SaaS companies"
                    }
                ]
            },
            "positioning": {
                "statement": "We help B2B marketers scale content"
            },
            "messaging": {
                "core_promise": "10x your content output"
            },
            "content_pillars": [
                {"name": "Thought Leadership", "description": "Industry insights"}
            ],
            "platform_plan": [
                {"platform": "LinkedIn", "goals": ["awareness"]}
            ],
            "cta_rules": {
                "allowed_ctas": ["Book a demo", "Download guide"]
            },
            "measurement": {
                "primary_kpis": ["MQLs", "Pipeline"]
            }
        }
        
        ok, errors, warnings = validate_strategy_contract(content)
        
        assert ok
        assert len(errors) == 0


class TestApprovalEnforcement:
    """Test that approve_artifact() enforces validation"""
    
    def setup_method(self):
        """Setup test session state"""
        self.session_state = {"_artifacts": {}}
        self.store = ArtifactStore(self.session_state, mode="inmemory")
    
    def test_approve_artifact_refuses_invalid_intake(self):
        """approve_artifact should refuse intake with validation errors"""
        # Create artifact with invalid content
        artifact = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test-client",
            engagement_id="test-engagement",
            content={"client_name": "Test"}  # Missing required fields
        )
        
        # Attempt approval - should raise validation error
        with pytest.raises(ArtifactValidationError) as exc_info:
            self.store.approve_artifact(artifact, approved_by="test")
        
        # Check error details
        assert len(exc_info.value.errors) >= 5  # Missing 5 required fields
    
    def test_approve_artifact_accepts_valid_intake(self):
        """approve_artifact should accept intake with valid content"""
        valid_content = {
            "client_name": "Test Client",
            "website": "https://example.com",
            "industry": "SaaS",
            "geography": "USA",
            "primary_offer": "Product Demo",
            "objective": "Leads"
        }
        
        artifact = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test-client",
            engagement_id="test-engagement",
            content=valid_content
        )
        
        # Should succeed
        approved = self.store.approve_artifact(artifact, approved_by="test")
        
        assert approved.status == ArtifactStatus.APPROVED
        assert approved.approved_by == "test"
        assert approved.approved_at is not None
    
    def test_approve_artifact_records_warnings(self):
        """approve_artifact should record warnings in artifact notes"""
        content = {
            "client_name": "Test Client",
            "website": "https://example.com",
            "industry": "Education",
            "geography": "USA",
            "primary_offer": "Course",
            "objective": "Leads",
            "target_audience": "students",
            "budget_range": "high-ticket"
        }
        
        artifact = self.store.create_artifact(
            artifact_type=ArtifactType.INTAKE,
            client_id="test-client",
            engagement_id="test-engagement",
            content=content
        )
        
        approved = self.store.approve_artifact(artifact, approved_by="test")
        
        assert approved.status == ArtifactStatus.APPROVED
        assert "approval_warnings" in approved.notes
        assert len(approved.notes["approval_warnings"]) > 0
