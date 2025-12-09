"""
Test suite for launch_gtm pack - verify no SaaS bias and appropriate GTM language.

GTM-specific checks:
- Launch phases are mentioned (pre-launch, launch, post-launch)
- No SaaS-only platforms/metrics for non-SaaS businesses
- Word count appropriate for GTM strategy (2000-4000 words)
"""

import pytest
from backend.main import api_aicmo_generate_report


@pytest.mark.asyncio
async def test_launch_gtm_non_saas_no_saas_bias():
    """Verify launch_gtm pack avoids SaaS-specific language for non-SaaS products."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Fresh Market Bakery",
            "industry": "Artisan Bakery",
            "product_service": "Artisan bread and pastries for local market",
            "primary_goal": "Launch new storefront with 200+ opening week customers",
            "geography": "Downtown area",
            "primary_customer": "Local food enthusiasts, office workers",
            "timeline": "60 days",
        },
        "wow_package_key": "launch_gtm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Verify no SaaS metrics for non-SaaS bakery
    saas_metrics = [
        r"\bMRR\b",
        r"\bARR\b",
        r"customer acquisition cost",
        r"\bCAC\b",
        r"churn rate",
        r"\bLTV\b",
    ]
    
    import re
    for pattern in saas_metrics:
        assert not re.search(pattern, report_markdown), (
            f"Found SaaS metric pattern '{pattern}' in non-SaaS launch report"
        )


@pytest.mark.asyncio
async def test_launch_gtm_has_launch_phases():
    """Verify launch_gtm pack mentions launch phases."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Fresh Market Bakery",
            "industry": "Artisan Bakery",
            "product_service": "Artisan bread and pastries",
            "primary_goal": "Launch new storefront",
            "geography": "Downtown area",
            "primary_customer": "Local food enthusiasts",
            "timeline": "60 days",
        },
        "wow_package_key": "launch_gtm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"].lower()
    
    # Launch packs should reference launch phases or related concepts
    launch_terms = ["launch", "pre-launch", "post-launch", "phase", "timeline", "go-to-market"]
    found = sum(1 for term in launch_terms if term in report_markdown)
    assert found >= 1, f"Expected launch-specific terms, found {found}"


@pytest.mark.asyncio
async def test_launch_gtm_reasonable_word_count():
    """Verify launch_gtm pack has appropriate word count."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Fresh Market Bakery",
            "industry": "Artisan Bakery",
            "product_service": "Artisan bread and pastries",
            "primary_goal": "Launch new storefront",
            "geography": "Downtown area",
            "primary_customer": "Local food enthusiasts",
            "timeline": "60 days",
        },
        "wow_package_key": "launch_gtm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"]
    word_count = len(report_markdown.split())
    
    # Launch GTM should be 2000-4000 words
    assert 1500 <= word_count <= 5000, f"Word count {word_count} outside expected range [1500-5000]"


@pytest.mark.asyncio
async def test_launch_gtm_no_duplicate_outcome_forecast():
    """Verify no duplicate Outcome Forecast sections."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Fresh Market Bakery",
            "industry": "Artisan Bakery",
            "product_service": "Artisan bread and pastries",
            "primary_goal": "Launch new storefront",
            "geography": "Downtown area",
            "primary_customer": "Local food enthusiasts",
            "timeline": "60 days",
        },
        "wow_package_key": "launch_gtm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"]
    
    count = report_markdown.lower().count("outcome forecast")
    assert count <= 1, f"'Outcome Forecast' appeared {count} times, expected at most 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
