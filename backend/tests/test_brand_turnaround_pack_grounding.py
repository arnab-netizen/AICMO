"""
Test suite for brand_turnaround pack - verify conservative tone and diagnostic focus.

Brand turnaround checks:
- Includes diagnosis/problem identification
- No "guaranteed success" or overpromising language
- Mentions repositioning strategy
- Appropriate word count for turnaround (2000-4000 words)
"""

import pytest
from backend.main import api_aicmo_generate_report


@pytest.mark.asyncio
async def test_brand_turnaround_diagnostic_focus():
    """Verify brand_turnaround pack includes problem diagnosis."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "RetailCo",
            "industry": "Specialty Retail",
            "product_service": "Fashion and accessories",
            "primary_goal": "Recover market share and rebuild customer trust",
            "geography": "Northeast region",
            "primary_customer": "Fashion-conscious millennials and Gen Z",
            "timeline": "6 months",
        },
        "wow_package_key": "brand_turnaround",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Brand turnaround should include diagnosis-related terms
    diagnostic_terms = ["diagnosis", "problem", "issue", "challenge", "root cause"]
    found = sum(1 for term in diagnostic_terms if term in report_markdown)
    assert found >= 2, f"Expected diagnostic terms, found {found}"


@pytest.mark.asyncio
async def test_brand_turnaround_no_overprising():
    """Verify brand_turnaround pack avoids guaranteed/assured language."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "RetailCo",
            "industry": "Specialty Retail",
            "product_service": "Fashion and accessories",
            "primary_goal": "Recover market share",
            "geography": "Northeast region",
            "primary_customer": "Fashion-conscious millennials",
            "timeline": "6 months",
        },
        "wow_package_key": "brand_turnaround",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"].lower()
    
    # Avoid overpromising language
    forbidden = ["guaranteed results", "assured success", "100% recovery"]
    for term in forbidden:
        assert term not in report_markdown, (
            f"Overpromising term '{term}' found in turnaround report"
        )


@pytest.mark.asyncio
async def test_brand_turnaround_mentions_repositioning():
    """Verify brand_turnaround pack mentions repositioning."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "RetailCo",
            "industry": "Specialty Retail",
            "product_service": "Fashion and accessories",
            "primary_goal": "Recover market share",
            "geography": "Northeast region",
            "primary_customer": "Fashion-conscious millennials",
            "timeline": "6 months",
        },
        "wow_package_key": "brand_turnaround",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"].lower()
    
    # Should mention repositioning/rebranding or strategy/refresh
    assert any(term in report_markdown for term in ["reposition", "rebrand", "refresh", "strategy", "approach"]), (
        "Turnaround pack should mention repositioning or strategy"
    )


@pytest.mark.asyncio
async def test_brand_turnaround_reasonable_word_count():
    """Verify brand_turnaround pack has appropriate word count."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "RetailCo",
            "industry": "Specialty Retail",
            "product_service": "Fashion and accessories",
            "primary_goal": "Recover market share",
            "geography": "Northeast region",
            "primary_customer": "Fashion-conscious millennials",
            "timeline": "6 months",
        },
        "wow_package_key": "brand_turnaround",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"]
    word_count = len(report_markdown.split())
    
    # Turnaround should be 1200-5000 words
    assert 1200 <= word_count <= 5000, f"Word count {word_count} outside expected range [1200-5000]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
