"""
Test defensive PDF rendering error handling.

Ensures that PDF rendering failures are caught and return structured errors
instead of crashing with unhandled exceptions.
"""

import pytest
from unittest.mock import patch
from backend.main import api_aicmo_generate_report
from backend.exceptions import PdfRenderError, BlankPdfError


@pytest.mark.asyncio
async def test_pdf_render_error_handled_gracefully():
    """
    Test that when PDF rendering fails, API returns structured error
    instead of raising unhandled exception.
    """
    payload = {
        "pack_key": "strategy_campaign_standard",
        "stage": "final",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Automotive",
            "primary_goal": "Increase showroom traffic",
        },
        "services": {
            "include_agency_grade": True,
        },
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
    }

    # Mock PDF renderer to raise error
    with patch("backend.pdf_renderer.render_agency_report_pdf") as mock_render:
        mock_render.side_effect = PdfRenderError("WeasyPrint failed to initialize")

        result = await api_aicmo_generate_report(payload)

        # Should return structured error, not raise exception
        assert "success" in result
        if not result["success"]:
            assert result["error_type"] in [
                "pdf_render_error",
                "agency_pipeline_error",
                "quality_gate_failed",
            ]
            assert "error_message" in result

    print("\n✅ PDF RENDER ERROR HANDLING TEST PASSED")
    print(f"   success: {result.get('success')}")
    print(f"   error_type: {result.get('error_type', 'N/A')}")


@pytest.mark.asyncio
async def test_blank_pdf_error_handled():
    """
    Test that BlankPdfError is caught and returns structured error.
    """
    payload = {
        "pack_key": "strategy_campaign_standard",
        "stage": "final",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Automotive",
            "primary_goal": "Increase showroom traffic",
        },
        "services": {
            "include_agency_grade": True,
        },
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
    }

    with patch("backend.pdf_renderer.render_agency_report_pdf") as mock_render:
        mock_render.side_effect = BlankPdfError("PDF generation returned empty bytes")

        result = await api_aicmo_generate_report(payload)

        # Should return blank_pdf error
        if not result["success"]:
            assert result["error_type"] in [
                "blank_pdf",
                "agency_pipeline_error",
                "quality_gate_failed",
            ]

    print("\n✅ BLANK PDF ERROR HANDLING TEST PASSED")
    print(f"   error_type: {result.get('error_type', 'N/A')}")


@pytest.mark.asyncio
async def test_weasyprint_import_error_handled():
    """
    Test that WeasyPrint import errors are handled gracefully.
    """
    payload = {
        "pack_key": "strategy_campaign_standard",
        "stage": "final",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Automotive",
            "primary_goal": "Increase showroom traffic",
        },
        "services": {
            "include_agency_grade": True,
        },
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
    }

    with patch("backend.pdf_renderer.render_agency_report_pdf") as mock_render:
        mock_render.side_effect = PdfRenderError("WeasyPrint is not available")

        result = await api_aicmo_generate_report(payload)

        # Should return structured error
        assert "success" in result
        if not result["success"]:
            assert "error_type" in result
            assert "error_message" in result

    print("\n✅ WEASYPRINT IMPORT ERROR HANDLING TEST PASSED")
    print(f"   success: {result.get('success')}")
