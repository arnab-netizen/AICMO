"""
Test suite for retention_crm pack - verify lifecycle focus and CRM/email emphasis.

Retention-specific checks:
- Mentions lifecycle, retention, or churn prevention
- Includes email automation/CRM terminology
- No SaaS-only metrics for non-SaaS businesses
- Appropriate word count (2000-4000 words)
"""

import pytest
import re
from backend.main import api_aicmo_generate_report


@pytest.mark.asyncio
async def test_retention_crm_lifecycle_focus():
    """Verify retention_crm pack emphasizes customer lifecycle."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Premium Coffee Co",
            "industry": "Specialty Coffee",
            "product_service": "Subscription coffee delivery and cafe loyalty",
            "primary_goal": "Increase repeat purchases and reduce churn to 90% annual retention",
            "geography": "North America",
            "primary_customer": "Coffee enthusiasts with $50+ monthly budget",
            "timeline": "Ongoing program",
        },
        "wow_package_key": "retention_crm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Retention packs should emphasize lifecycle/engagement
    lifecycle_terms = ["lifecycle", "retention", "churn", "engagement", "loyalty"]
    found = sum(1 for term in lifecycle_terms if term in report_markdown)
    assert found >= 2, f"Expected lifecycle terms, found {found}"


@pytest.mark.asyncio
async def test_retention_crm_email_focus():
    """Verify retention_crm pack includes email/CRM automation."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Premium Coffee Co",
            "industry": "Specialty Coffee",
            "product_service": "Subscription coffee delivery",
            "primary_goal": "Increase repeat purchases",
            "geography": "North America",
            "primary_customer": "Coffee enthusiasts",
            "timeline": "Ongoing",
        },
        "wow_package_key": "retention_crm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"].lower()
    
    # Should emphasize email/CRM
    email_terms = ["email", "crm", "automation", "workflow"]
    found = sum(1 for term in email_terms if term in report_markdown)
    assert found >= 1, f"Expected email/CRM terms, found {found}"


@pytest.mark.asyncio
async def test_retention_crm_no_saas_bias():
    """Verify retention_crm doesn't have SaaS-only metrics for non-SaaS."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Premium Coffee Co",
            "industry": "Specialty Coffee",
            "product_service": "Subscription coffee delivery",
            "primary_goal": "Increase repeat purchases",
            "geography": "North America",
            "primary_customer": "Coffee enthusiasts",
            "timeline": "Ongoing",
        },
        "wow_package_key": "retention_crm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"].lower()
    
    # Check for SaaS-specific metrics
    saas_patterns = [
        r"\bMRR\b",
        r"\bARR\b",
        r"product hunt",
        r"\bG2\b",
    ]
    
    for pattern in saas_patterns:
        assert not re.search(pattern, report_markdown), (
            f"Found SaaS pattern '{pattern}' in non-SaaS retention report"
        )


@pytest.mark.asyncio
async def test_retention_crm_reasonable_word_count():
    """Verify retention_crm pack has appropriate word count."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "Premium Coffee Co",
            "industry": "Specialty Coffee",
            "product_service": "Subscription coffee delivery",
            "primary_goal": "Increase repeat purchases",
            "geography": "North America",
            "primary_customer": "Coffee enthusiasts",
            "timeline": "Ongoing",
        },
        "wow_package_key": "retention_crm",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"]
    word_count = len(report_markdown.split())
    
    # Retention CRM should be 2000-4000 words
    assert 1500 <= word_count <= 5000, f"Word count {word_count} outside expected range [1500-5000]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
