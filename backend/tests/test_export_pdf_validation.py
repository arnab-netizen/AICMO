"""
Test PDF export validation.

Verify that PDF export now validates markdown for placeholders before exporting,
matching the behavior of PPTX and ZIP exports.

Added as part of Export Safety Audit (docs/EXPORT_SAFETY_AUDIT_REPORT.md).
"""

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


class TestPDFExportValidation:
    """PDF export validation guard tests."""

    def test_aicmo_export_pdf_blocks_placeholder_pattern(self):
        """
        PDF export should be blocked if markdown contains known placeholder patterns.

        This test verifies that safe_export_pdf(markdown, check_placeholders=True)
        validation is now active in the API endpoint.
        """
        payload = {"markdown": "Campaign Strategy:\n[PLACEHOLDER]\n\nBudget: TBD\n"}

        resp = client.post("/aicmo/export/pdf", json=payload)

        # Should be blocked with a 400 error
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, dict), f"Expected dict response, got {type(data)}"
        assert data.get("error") is True, f"Expected error=True, got {data}"

    def test_aicmo_export_pdf_blocks_tbd_pattern(self):
        """TBD pattern should block PDF export."""
        payload = {"markdown": "Budget Information: TBD\nTimeline: TBD"}

        resp = client.post("/aicmo/export/pdf", json=payload)

        assert resp.status_code == 400
        data = resp.json()
        assert data.get("error") is True

    def test_aicmo_export_pdf_allows_clean_markdown(self):
        """
        PDF export should succeed for clean markdown without placeholders.

        Verifies that non-placeholder content exports normally without
        being incorrectly blocked.
        """
        payload = {
            "markdown": "Campaign Strategy:\nOur approach is to focus on digital channels.\n\nBudget: $50,000\nTimeline: 3 months"
        }

        resp = client.post("/aicmo/export/pdf", json=payload)

        # For successful export, FastAPI returns StreamingResponse
        # Status code should be 200 and content-type should be PDF
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert (
            "application/pdf" in resp.headers.get("content-type", "").lower()
        ), f"Expected PDF content-type, got {resp.headers.get('content-type')}"

    def test_aicmo_export_pdf_allows_legitimate_bracket_content(self):
        """
        PDF export should allow legitimate use of brackets in content.

        Brackets are used in legitimate marketing content; the validation
        should only block specific placeholder patterns, not all brackets.
        """
        payload = {
            "markdown": "Email Campaign [Q1 Launch]:\nTarget audience aged [25-34] years old.\nStrategy uses [Email, SMS, Social Media]."
        }

        resp = client.post("/aicmo/export/pdf", json=payload)

        # This should succeed because these are not placeholder patterns
        assert resp.status_code == 200
        assert "application/pdf" in resp.headers.get("content-type", "").lower()

    def test_aicmo_export_pdf_blocks_performance_review_placeholder(self):
        """
        Known placeholder pattern 'Performance review will be populated' should block export.
        """
        payload = {
            "markdown": "Agency Performance:\nPerformance review will be populated with data."
        }

        resp = client.post("/aicmo/export/pdf", json=payload)

        assert resp.status_code == 400
        data = resp.json()
        assert data.get("error") is True

    def test_aicmo_export_pdf_blocks_hook_idea_placeholder(self):
        """
        Known placeholder pattern 'Hook idea for day' should block export.
        """
        payload = {
            "markdown": "Daily Creative:\nHook idea for day 1 will be customized for the audience."
        }

        resp = client.post("/aicmo/export/pdf", json=payload)

        assert resp.status_code == 400
        data = resp.json()
        assert data.get("error") is True

    def test_aicmo_export_pdf_empty_markdown_returns_error(self):
        """Empty markdown should return an error."""
        payload = {"markdown": ""}

        resp = client.post("/aicmo/export/pdf", json=payload)

        assert resp.status_code == 400
        data = resp.json()
        assert data.get("error") is True

    def test_aicmo_export_pdf_missing_markdown_returns_error(self):
        """Missing markdown key should return an error."""
        payload = {}

        resp = client.post("/aicmo/export/pdf", json=payload)

        assert resp.status_code == 400
        data = resp.json()
        assert data.get("error") is True

    def test_aicmo_export_pdf_blocks_multiple_placeholder_types(self):
        """
        PDF export should block if markdown contains multiple types of placeholders.
        """
        payload = {
            "markdown": (
                "Strategy: [PLACEHOLDER]\n"
                "Budget: TBD\n"
                "Timeline: Performance review will be populated\n"
                "Creative: Hook idea for day 1"
            )
        }

        resp = client.post("/aicmo/export/pdf", json=payload)

        assert resp.status_code == 400
        data = resp.json()
        assert data.get("error") is True
