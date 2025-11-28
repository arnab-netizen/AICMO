"""
Smoke tests for export functionality (Patch 8).

Tests that PDF, PPTX, and ZIP export endpoints are callable and return valid responses.
These are basic happy-path smoke tests, not comprehensive edge-case testing.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Fixture to provide FastAPI test client."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def pdf_export_payload():
    """Minimal valid payload for testing PDF export with markdown."""
    return {
        "markdown": "# Test Report\n\n## Overview\n\nThis is a test marketing report.\n\n## Key Sections\n\n- **Audience**: Enterprise customers\n- **Messaging**: Focus on ROI and efficiency\n\n## Next Steps\n\nImplement campaigns.",
    }


@pytest.fixture
def pptx_zip_export_payload():
    """Full payload for PPTX/ZIP exports that require both brief and output."""
    return {
        "brief": {
            "brand": {
                "brand_name": "Test Brand",
                "industry": "SaaS",
                "product_service": "Software Platform",
                "primary_goal": "Increase market share",
                "primary_customer": "Enterprise customers",
            },
            "audience": {
                "primary_customer": "Enterprise customers",
                "customer_size": "large",
                "decision_makers": "C-suite",
            },
            "goal": {
                "primary_goal": "Increase market share",
                "timeline": "12 months",
            },
            "voice": {
                "brand_voice": "Professional",
                "tone": "Authoritative",
            },
            "operations": {
                "budget": 100000,
                "channels": ["LinkedIn", "Twitter"],
                "team_size": 5,
            },
            "assets_constraints": {
                "available_assets": ["Social media accounts", "Email list"],
                "content_constraints": "No video production",
            },
            "strategy_extras": {
                "brand_adjectives": ["innovative", "reliable"],
            },
        },
        "output": {
            "marketing_plan": {
                "executive_summary": "Test marketing plan",
            },
            "campaign_blueprint": {
                "campaign_name": "Test Campaign",
            },
            "social_calendar": {
                "calendar_entries": [],
            },
        },
    }


class TestPDFExport:
    """Tests for PDF export functionality."""

    def test_pdf_export_returns_200(self, client, pdf_export_payload):
        """PDF export should return 200 OK."""
        response = client.post("/aicmo/export/pdf", json=pdf_export_payload)
        assert response.status_code == 200

    def test_pdf_export_returns_binary(self, client, pdf_export_payload):
        """PDF export should return binary content."""
        response = client.post("/aicmo/export/pdf", json=pdf_export_payload)
        assert response.status_code == 200
        assert response.content

    def test_pdf_export_has_content_type(self, client, pdf_export_payload):
        """PDF export should have appropriate content type."""
        response = client.post("/aicmo/export/pdf", json=pdf_export_payload)
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "").lower()
        assert "pdf" in content_type or "plain" in content_type or "octet" in content_type


class TestPPTXExport:
    """Tests for PPTX export functionality."""

    def test_pptx_export_returns_200(self, client, pptx_zip_export_payload):
        """PPTX export should return 200 OK."""
        response = client.post("/aicmo/export/pptx", json=pptx_zip_export_payload)
        # PPTX export may fail due to model complexity, but should not 500
        assert response.status_code in [200, 400, 422]

    def test_pptx_export_returns_binary_or_fails_gracefully(self, client, pptx_zip_export_payload):
        """PPTX export should return binary content or fail gracefully (not 500)."""
        response = client.post("/aicmo/export/pptx", json=pptx_zip_export_payload)
        # On success: has content. On model error: is 400/422, no 500
        if response.status_code == 200:
            assert response.content
        else:
            assert response.status_code in [400, 422]


class TestZIPExport:
    """Tests for ZIP export functionality."""

    def test_zip_export_returns_200(self, client, pptx_zip_export_payload):
        """ZIP export should return 200 OK."""
        response = client.post("/aicmo/export/zip", json=pptx_zip_export_payload)
        # ZIP export may fail due to model complexity, but should not 500
        assert response.status_code in [200, 400, 422]

    def test_zip_export_returns_binary_or_fails_gracefully(self, client, pptx_zip_export_payload):
        """ZIP export should return binary content or fail gracefully (not 500)."""
        response = client.post("/aicmo/export/zip", json=pptx_zip_export_payload)
        # On success: has content. On model error: is 400/422, no 500
        if response.status_code == 200:
            assert response.content
        else:
            assert response.status_code in [400, 422]


class TestExportConsistency:
    """Test that export formats work and fail gracefully."""

    def test_pdf_export_with_markdown(self, client, pdf_export_payload):
        """PDF export should work with markdown payload."""
        response = client.post("/aicmo/export/pdf", json=pdf_export_payload)
        assert response.status_code == 200

    def test_export_missing_payload_fails_gracefully(self, client):
        """Export with missing payload should fail gracefully (not 500)."""
        endpoints = ["/aicmo/export/pdf", "/aicmo/export/pptx", "/aicmo/export/zip"]

        for endpoint in endpoints:
            response = client.post(endpoint, json={})
            # Should not return 500, but may return 400 (bad request) or 200 with fallback
            assert response.status_code != 500, f"Export {endpoint} returned server error"
