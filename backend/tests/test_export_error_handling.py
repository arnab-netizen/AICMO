"""
Tests for export error handling.

Tests cover:
1. PDF export with empty/invalid content
2. PPTX export with missing fields
3. ZIP export with various edge cases
4. Graceful error responses for all export types
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from aicmo.io.client_reports import (
    ClientInputBrief,
    AICMOOutputReport,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
    MarketingPlanView,
    StrategyPillar,
    CampaignBlueprintView,
    CampaignObjectiveView,
    AudiencePersonaView,
    SocialCalendarView,
    CalendarPostView,
    ActionPlan,
)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def minimal_brief():
    """Create a minimal valid brief."""
    return ClientInputBrief(
        brand=BrandBrief(brand_name="Test Brand"),
        audience=AudienceBrief(primary_customer="Test Customer"),
        goal=GoalBrief(primary_goal="Test Goal"),
        voice=VoiceBrief(),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


@pytest.fixture
def minimal_output():
    """Create a minimal valid output report that passes agency-grade validation."""
    from datetime import date, timedelta

    return AICMOOutputReport(
        marketing_plan=MarketingPlanView(
            executive_summary="Strategic overview of the marketing approach",
            situation_analysis="Market analysis and positioning",
            strategy="Comprehensive strategy statement",
            pillars=[
                StrategyPillar(name="Pillar One", description="First strategic focus area"),
                StrategyPillar(name="Pillar Two", description="Second strategic focus area"),
                StrategyPillar(name="Pillar Three", description="Third strategic focus area"),
            ],
        ),
        campaign_blueprint=CampaignBlueprintView(
            big_idea="Compelling campaign concept",
            objective=CampaignObjectiveView(primary="awareness"),
            audience_persona=AudiencePersonaView(name="Test", description="Test"),
        ),
        social_calendar=SocialCalendarView(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            posts=[
                CalendarPostView(
                    date=date.today() + timedelta(days=i),
                    platform="Instagram",
                    theme="Theme",
                    hook=f"Hook for day {i+1}",
                    cta="Learn more",
                    asset_type="carousel",
                )
                for i in range(7)
            ],
        ),
        action_plan=ActionPlan(
            quick_wins=["Action 1"],
            next_10_days=["Action 2"],
            next_30_days=["Action 3", "Action 4", "Action 5"],
        ),
    )


class TestPDFExport:
    """Tests for PDF export error handling."""

    def test_pdf_export_empty_markdown(self, client):
        """PDF export should handle empty markdown gracefully."""
        response = client.post("/aicmo/export/pdf", json={"markdown": ""})
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert "empty" in data["message"].lower()
        assert data["export_type"] == "pdf"

    def test_pdf_export_whitespace_only(self, client):
        """PDF export should handle whitespace-only markdown gracefully."""
        response = client.post("/aicmo/export/pdf", json={"markdown": "   \n\n   "})
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_pdf_export_valid_markdown(self, client):
        """PDF export should succeed with valid markdown."""
        markdown = "# Test Report\n\n## Section 1\n\nSome content here."
        response = client.post("/aicmo/export/pdf", json={"markdown": markdown})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    def test_pdf_export_missing_markdown_key(self, client):
        """PDF export should handle missing markdown key."""
        response = client.post("/aicmo/export/pdf", json={})
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True


class TestPPTXExport:
    """Tests for PPTX export error handling."""

    def test_pptx_export_empty_payload(self, client):
        """PPTX export should handle empty payload."""
        response = client.post("/aicmo/export/pptx", json={})
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["export_type"] == "pptx"

    def test_pptx_export_invalid_brief(self, client, minimal_output):
        """PPTX export should handle invalid brief format."""
        response = client.post(
            "/aicmo/export/pptx",
            json={
                "brief": {"invalid": "format"},
                "output": minimal_output.model_dump(mode="json"),
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_pptx_export_invalid_output(self, client, minimal_brief):
        """PPTX export should handle invalid output format."""
        response = client.post(
            "/aicmo/export/pptx",
            json={
                "brief": minimal_brief.model_dump(),
                "output": {"invalid": "format"},
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_pptx_export_valid(self, client, minimal_brief, minimal_output):
        """PPTX export should succeed with valid input."""
        response = client.post(
            "/aicmo/export/pptx",
            json={
                "brief": minimal_brief.model_dump(mode="json"),
                "output": minimal_output.model_dump(mode="json"),
            },
        )
        assert response.status_code == 200
        assert "presentation" in response.headers["content-type"]
        assert len(response.content) > 0


class TestZIPExport:
    """Tests for ZIP export error handling."""

    def test_zip_export_empty_payload(self, client):
        """ZIP export should handle empty payload."""
        response = client.post("/aicmo/export/zip", json={})
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["export_type"] == "zip"

    def test_zip_export_invalid_brief(self, client, minimal_output):
        """ZIP export should handle invalid brief format."""
        response = client.post(
            "/aicmo/export/zip",
            json={
                "brief": {"invalid": "format"},
                "output": minimal_output.model_dump(mode="json"),
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_zip_export_invalid_output(self, client, minimal_brief):
        """ZIP export should handle invalid output."""
        response = client.post(
            "/aicmo/export/zip",
            json={
                "brief": minimal_brief.model_dump(),
                "output": {"invalid": "format"},
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_zip_export_valid(self, client, minimal_brief, minimal_output):
        """ZIP export should succeed with valid input."""
        response = client.post(
            "/aicmo/export/zip",
            json={
                "brief": minimal_brief.model_dump(mode="json"),
                "output": minimal_output.model_dump(mode="json"),
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert len(response.content) > 0

    def test_zip_export_with_creatives(self, client, minimal_brief, minimal_output):
        """ZIP export should include creatives when present."""
        from aicmo.io.client_reports import CreativesBlock

        minimal_output.creatives = CreativesBlock(
            hooks=["Hook 1", "Hook 2"],
            captions=["Caption 1"],
            scripts=["Script 1"],
            email_subject_lines=["Subject 1"],
        )

        response = client.post(
            "/aicmo/export/zip",
            json={
                "brief": minimal_brief.model_dump(mode="json"),
                "output": minimal_output.model_dump(mode="json"),
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        # Verify ZIP contains creatives files
        import zipfile
        import io

        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf, "r") as z:
            assert "02_Creatives/hooks.txt" in z.namelist()
            assert "02_Creatives/captions.txt" in z.namelist()


class TestExportErrorHandling:
    """Integration tests for error handling across all export types."""

    def test_all_exports_handle_errors_gracefully(self, client):
        """All export endpoints should return JSON errors, not 500 exceptions."""
        endpoints = [
            "/aicmo/export/pdf",
            "/aicmo/export/pptx",
            "/aicmo/export/zip",
        ]

        for endpoint in endpoints:
            response = client.post(endpoint, json={})
            # Should return 400 (bad request), not 500 (server error)
            assert response.status_code == 400, f"{endpoint} did not handle error gracefully"
            # Should be valid JSON with error details
            data = response.json()
            assert "error" in data
            assert "message" in data
            assert "export_type" in data
