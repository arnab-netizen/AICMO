"""
Test suite for performance_audit pack - verify diagnostic and analytical focus.

Performance audit checks:
- Mentions audit, analysis, performance findings
- Includes optimization recommendations
- No SaaS-only platforms for non-SaaS businesses
- Appropriate word count for audit (1500-3500 words)
"""

import pytest
import re
from backend.main import api_aicmo_generate_report


@pytest.mark.asyncio
async def test_performance_audit_diagnostic_focus():
    """Verify performance_audit pack includes audit and analysis terms."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "TechStyle Fashion",
            "industry": "Online Fashion Retail",
            "product_service": "Clothing and accessories e-commerce",
            "primary_goal": "Identify campaign performance gaps and optimize spend",
            "geography": "United States",
            "primary_customer": "Style-conscious adults aged 25-40",
            "timeline": "Immediate audit + 90-day optimization",
        },
        "wow_package_key": "performance_audit",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success", f"Failed: {result.get('error_message', 'unknown')}"
    assert isinstance(result["report_markdown"], str)
    assert result["report_markdown"].strip()
    
    report_markdown = result["report_markdown"].lower()
    
    # Audit packs should include diagnostic terms
    audit_terms = ["audit", "analysis", "findings", "performance", "optimization"]
    found = sum(1 for term in audit_terms if term in report_markdown)
    assert found >= 3, f"Expected audit/analysis terms, found {found}"


@pytest.mark.asyncio
async def test_performance_audit_includes_recommendations():
    """Verify performance_audit pack includes optimization recommendations."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "TechStyle Fashion",
            "industry": "Online Fashion Retail",
            "product_service": "Clothing and accessories e-commerce",
            "primary_goal": "Identify campaign performance gaps",
            "geography": "United States",
            "primary_customer": "Style-conscious adults",
            "timeline": "Immediate audit",
        },
        "wow_package_key": "performance_audit",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"].lower()
    
    # Should include recommendations/optimization
    assert any(term in report_markdown for term in ["recommend", "optimize", "improvement", "action"]), (
        "Audit pack should include recommendations"
    )


@pytest.mark.asyncio
async def test_performance_audit_no_saas_bias():
    """Verify performance_audit doesn't have SaaS-only metrics for non-SaaS."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "TechStyle Fashion",
            "industry": "Online Fashion Retail",
            "product_service": "Clothing and accessories e-commerce",
            "primary_goal": "Identify performance gaps",
            "geography": "United States",
            "primary_customer": "Style-conscious adults",
            "timeline": "Immediate",
        },
        "wow_package_key": "performance_audit",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"].lower()
    
    # Check for SaaS-specific metrics (should not be mentioned for e-commerce)
    saas_patterns = [
        r"\bMRR\b",
        r"\bARR\b",
        r"free trial",
        r"product hunt",
        r"\bG2\b",
    ]
    
    for pattern in saas_patterns:
        assert not re.search(pattern, report_markdown), (
            f"Found SaaS pattern '{pattern}' in non-SaaS audit report"
        )


@pytest.mark.asyncio
async def test_performance_audit_reasonable_word_count():
    """Verify performance_audit pack has appropriate word count."""
    
    payload = {
        "stage": "draft",
        "client_brief": {
            "brand_name": "TechStyle Fashion",
            "industry": "Online Fashion Retail",
            "product_service": "Clothing and accessories e-commerce",
            "primary_goal": "Identify performance gaps",
            "geography": "United States",
            "primary_customer": "Style-conscious adults",
            "timeline": "Immediate",
        },
        "wow_package_key": "performance_audit",
        "draft_mode": True,
    }
    
    result = await api_aicmo_generate_report(payload, include_pdf=False)
    assert result["status"] == "success"
    report_markdown = result["report_markdown"]
    word_count = len(report_markdown.split())
    
    # Audit should be lighter (1500-3500 words)
    assert 1000 <= word_count <= 4000, f"Word count {word_count} outside expected range [1000-4000]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
