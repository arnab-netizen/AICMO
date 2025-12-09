"""Tests for Client Portal & Approvals Engine.

Stage CP: Portal engine tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import tempfile
import os

from aicmo.domain.intake import ClientIntake
from aicmo.portal.domain import (
    ApprovalStatus,
    AssetType,
    FeedbackPriority,
    ApprovalRequest,
    ClientFeedback,
    AssetVersion,
    PortalAccess,
    ApprovalSummary,
)
from aicmo.portal.service import (
    create_approval_request,
    submit_client_feedback,
    create_asset_version,
    grant_portal_access,
    generate_approval_summary,
    approve_request,
    request_changes,
)
from aicmo.learning.event_types import EventType


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_intake():
    """Sample client intake for testing."""
    return ClientIntake(
        brand_name="PortalTestCo",
        industry="Marketing",
        product_service="Digital marketing services",
        primary_goal="Streamline approval process",
        target_audiences=["Marketing managers"]
    )


@pytest.fixture
def sample_approval_request():
    """Sample approval request for testing."""
    return ApprovalRequest(
        request_id="req-1",
        brand_name="PortalTestCo",
        asset_type=AssetType.CREATIVE,
        asset_name="Summer Campaign Creative",
        asset_url="https://example.com/asset.jpg",
        asset_version=1,
        status=ApprovalStatus.PENDING,
        requested_by="designer@agency.com",
        requested_at=datetime.now(),
        assigned_reviewers=["client@brand.com"],
        due_date=datetime.now() + timedelta(days=3)
    )


# ═══════════════════════════════════════════════════════════════════════
# Domain Model Tests
# ═══════════════════════════════════════════════════════════════════════


class TestApprovalRequestDomain:
    """Test ApprovalRequest domain model."""
    
    def test_approval_request_creation(self, sample_approval_request):
        """Test creating an approval request."""
        assert sample_approval_request.status == ApprovalStatus.PENDING
        assert sample_approval_request.asset_type == AssetType.CREATIVE
        assert len(sample_approval_request.assigned_reviewers) == 1


class TestClientFeedbackDomain:
    """Test ClientFeedback domain model."""
    
    def test_feedback_creation(self):
        """Test creating client feedback."""
        feedback = ClientFeedback(
            feedback_id="fb-1",
            approval_request_id="req-1",
            brand_name="TestBrand",
            reviewer_name="John Client",
            reviewer_email="john@client.com",
            feedback_text="Please adjust the color scheme",
            priority=FeedbackPriority.HIGH,
            is_addressed=False,
            created_at=datetime.now()
        )
        
        assert feedback.priority == FeedbackPriority.HIGH
        assert not feedback.is_addressed


class TestAssetVersionDomain:
    """Test AssetVersion domain model."""
    
    def test_version_creation(self):
        """Test creating an asset version."""
        version = AssetVersion(
            version_id="ver-1",
            approval_request_id="req-1",
            version_number=2,
            asset_url="https://example.com/asset_v2.jpg",
            change_summary="Updated colors per client feedback",
            changed_by="designer@agency.com",
            created_at=datetime.now(),
            addressed_feedback_ids=["fb-1", "fb-2"]
        )
        
        assert version.version_number == 2
        assert len(version.addressed_feedback_ids) == 2


# ═══════════════════════════════════════════════════════════════════════
# Service Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestApprovalRequestCreation:
    """Test approval request creation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_create_request_returns_request(self, temp_db, sample_intake):
        """Test that create_approval_request returns request."""
        request = create_approval_request(
            sample_intake,
            asset_type=AssetType.CREATIVE,
            asset_name="Test Creative",
            asset_url="https://example.com/test.jpg",
            requested_by="designer@agency.com",
            reviewers=["client@brand.com"]
        )
        
        assert isinstance(request, ApprovalRequest)
        assert request.brand_name == sample_intake.brand_name
        assert request.status == ApprovalStatus.PENDING
    
    def test_request_has_due_date(self, temp_db, sample_intake):
        """Test that request includes due date."""
        request = create_approval_request(
            sample_intake,
            asset_type=AssetType.REPORT,
            asset_name="Monthly Report",
            asset_url="https://example.com/report.pdf",
            requested_by="analyst@agency.com",
            reviewers=["manager@brand.com"],
            due_days=5
        )
        
        assert request.due_date is not None
        assert request.due_date > datetime.now()
    
    def test_request_logs_event(self, temp_db, sample_intake):
        """Test that request creation logs learning event."""
        with patch('aicmo.portal.service.log_event') as mock_log:
            create_approval_request(
                sample_intake,
                asset_type=AssetType.VIDEO,
                asset_name="Product Video",
                asset_url="https://example.com/video.mp4",
                requested_by="producer@agency.com",
                reviewers=["client@brand.com"]
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.CLIENT_APPROVAL_REQUESTED.value


class TestClientFeedbackSubmission:
    """Test client feedback submission."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_submit_feedback_returns_feedback(self, temp_db):
        """Test that submit_client_feedback returns feedback."""
        feedback = submit_client_feedback(
            approval_request_id="req-123",
            brand_name="TestBrand",
            reviewer_name="Jane Client",
            reviewer_email="jane@client.com",
            feedback_text="Great work, just minor tweaks needed",
            priority=FeedbackPriority.LOW
        )
        
        assert isinstance(feedback, ClientFeedback)
        assert feedback.reviewer_name == "Jane Client"
        assert feedback.priority == FeedbackPriority.LOW
    
    def test_feedback_not_addressed_initially(self, temp_db):
        """Test that feedback is not addressed initially."""
        feedback = submit_client_feedback(
            approval_request_id="req-123",
            brand_name="TestBrand",
            reviewer_name="Client",
            reviewer_email="client@brand.com",
            feedback_text="Please revise"
        )
        
        assert not feedback.is_addressed
        assert feedback.addressed_by is None
    
    def test_feedback_logs_event(self, temp_db):
        """Test that feedback submission logs learning event."""
        with patch('aicmo.portal.service.log_event') as mock_log:
            submit_client_feedback(
                approval_request_id="req-123",
                brand_name="TestBrand",
                reviewer_name="Client",
                reviewer_email="client@brand.com",
                feedback_text="Test feedback"
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.CLIENT_COMMENT_RECEIVED.value


class TestAssetVersioning:
    """Test asset version creation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_create_version_returns_version(self, temp_db):
        """Test that create_asset_version returns version."""
        version = create_asset_version(
            approval_request_id="req-123",
            version_number=2,
            asset_url="https://example.com/asset_v2.jpg",
            change_summary="Revised based on feedback",
            changed_by="designer@agency.com",
            addressed_feedback_ids=["fb-1"]
        )
        
        assert isinstance(version, AssetVersion)
        assert version.version_number == 2
        assert len(version.addressed_feedback_ids) == 1
    
    def test_version_logs_event(self, temp_db):
        """Test that version creation logs learning event."""
        with patch('aicmo.portal.service.log_event') as mock_log:
            create_asset_version(
                approval_request_id="req-123",
                version_number=2,
                asset_url="https://example.com/v2.jpg",
                change_summary="Updated",
                changed_by="designer@agency.com"
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.CLIENT_APPROVAL_RESPONDED.value


class TestPortalAccess:
    """Test portal access management."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_grant_access_returns_access(self, temp_db):
        """Test that grant_portal_access returns access record."""
        access = grant_portal_access(
            brand_name="TestBrand",
            user_email="client@brand.com",
            user_name="Client User",
            user_role="client",
            can_approve=True
        )
        
        assert isinstance(access, PortalAccess)
        assert access.can_approve is True
        assert access.is_active is True
    
    def test_access_logs_event(self, temp_db):
        """Test that access grant logs learning event."""
        with patch('aicmo.portal.service.log_event') as mock_log:
            grant_portal_access(
                brand_name="TestBrand",
                user_email="user@brand.com",
                user_name="User",
                user_role="stakeholder"
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.CLIENT_PORTAL_ACCESSED.value


class TestApprovalSummary:
    """Test approval summary generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_summary_returns_summary(self, temp_db, sample_intake):
        """Test that generate_approval_summary returns summary."""
        summary = generate_approval_summary(sample_intake, days_back=30)
        
        assert isinstance(summary, ApprovalSummary)
        assert summary.brand_name == sample_intake.brand_name
        assert summary.total_requests > 0
    
    def test_summary_has_metrics(self, temp_db, sample_intake):
        """Test that summary includes key metrics."""
        summary = generate_approval_summary(sample_intake)
        
        assert summary.avg_approval_time_hours > 0
        assert len(summary.requests_by_type) > 0
        assert len(summary.approval_rate_by_type) > 0
    
    def test_summary_logs_event(self, temp_db, sample_intake):
        """Test that summary generation logs learning event."""
        with patch('aicmo.portal.service.log_event') as mock_log:
            generate_approval_summary(sample_intake)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.CLIENT_APPROVAL_APPROVED.value


class TestApprovalActions:
    """Test approval action helpers."""
    
    def test_approve_request_updates_status(self, sample_approval_request):
        """Test that approve_request updates status."""
        approved = approve_request(
            sample_approval_request,
            reviewer_name="Client Reviewer",
            approval_notes="Looks great!"
        )
        
        assert approved.status == ApprovalStatus.APPROVED
        assert approved.reviewed_by == "Client Reviewer"
        assert approved.reviewed_at is not None
    
    def test_request_changes_updates_status(self, sample_approval_request):
        """Test that request_changes updates status."""
        revised = request_changes(
            sample_approval_request,
            reviewer_name="Client Reviewer",
            change_notes="Please adjust colors"
        )
        
        assert revised.status == ApprovalStatus.CHANGES_REQUESTED
        assert revised.reviewed_by == "Client Reviewer"


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestPortalEngineIntegration:
    """Test portal engine integration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_complete_approval_workflow(self, temp_db):
        """Test complete approval workflow."""
        # Create intake
        intake = ClientIntake(
            brand_name="WorkflowTest",
            industry="Technology",
            product_service="SaaS platform",
            primary_goal="Launch campaign",
            target_audiences=["Tech users"]
        )
        
        # Grant portal access
        access = grant_portal_access(
            brand_name=intake.brand_name,
            user_email="client@test.com",
            user_name="Test Client",
            user_role="approver",
            can_approve=True
        )
        assert access.can_approve
        
        # Create approval request
        request = create_approval_request(
            intake,
            asset_type=AssetType.CREATIVE,
            asset_name="Launch Creative",
            asset_url="https://example.com/creative.jpg",
            requested_by="designer@agency.com",
            reviewers=["client@test.com"]
        )
        assert request.status == ApprovalStatus.PENDING
        
        # Submit feedback
        feedback = submit_client_feedback(
            approval_request_id=request.request_id,
            brand_name=intake.brand_name,
            reviewer_name="Test Client",
            reviewer_email="client@test.com",
            feedback_text="Please adjust the headline",
            priority=FeedbackPriority.HIGH
        )
        assert not feedback.is_addressed
        
        # Create revised version
        version = create_asset_version(
            approval_request_id=request.request_id,
            version_number=2,
            asset_url="https://example.com/creative_v2.jpg",
            change_summary="Adjusted headline per feedback",
            changed_by="designer@agency.com",
            addressed_feedback_ids=[feedback.feedback_id]
        )
        assert version.version_number == 2
        
        # Approve request
        approved = approve_request(request, "Test Client", "Perfect!")
        assert approved.status == ApprovalStatus.APPROVED
        
        # Generate summary
        summary = generate_approval_summary(intake)
        assert summary.total_requests > 0
