"""Phase 1 tests: Strategy service wrapper implementation.

Verifies that:
1. New aicmo.strategy.service works correctly
2. ClientIntake → ClientInputBrief conversion works
3. StrategyDoc output is properly structured
4. No breaking changes to existing backend behavior
"""

import pytest
from unittest.mock import AsyncMock, patch

from aicmo.domain.intake import ClientIntake
from aicmo.domain.strategy import StrategyDoc, StrategyPillar
from aicmo.strategy.service import generate_strategy
from aicmo.io.client_reports import MarketingPlanView, StrategyPillar as BackendPillar


class TestPhase1StrategyService:
    """Phase 1: Strategy service wrapper tests."""

    def test_client_intake_to_brief_conversion(self):
        """ClientIntake.to_client_input_brief() creates valid backend format."""
        intake = ClientIntake(
            brand_name="Test Co",
            industry="Technology",
            product_service="SaaS Platform",
            primary_customer="Enterprise buyers",
            primary_goal="Increase leads by 50%",
            timeline="Q1 2024",
            geography="North America"
        )

        brief = intake.to_client_input_brief()

        # Verify structure
        assert brief.brand.brand_name == "Test Co"
        assert brief.brand.industry == "Technology"
        assert brief.brand.product_service == "SaaS Platform"
        assert brief.brand.primary_customer == "Enterprise buyers"
        assert brief.goal.primary_goal == "Increase leads by 50%"
        assert brief.goal.timeline == "Q1 2024"
        assert brief.brand.location == "North America"

    def test_client_intake_with_defaults(self):
        """ClientIntake handles missing optional fields gracefully."""
        intake = ClientIntake(
            brand_name="Minimal Co",
        )

        brief = intake.to_client_input_brief()

        # Should have safe defaults
        assert brief.brand.brand_name == "Minimal Co"
        assert brief.brand.industry == "General"
        assert brief.brand.product_service == "Products and services"
        assert brief.goal.timeline == "90 days"

    @pytest.mark.asyncio
    async def test_generate_strategy_wrapper(self):
        """generate_strategy() wraps backend and returns StrategyDoc."""
        intake = ClientIntake(
            brand_name="Strategy Test Co",
            industry="FinTech",
            primary_goal="Drive awareness",
            timeline="6 months"
        )

        # Mock the backend function
        mock_marketing_plan = MarketingPlanView(
            executive_summary="Test summary for Strategy Test Co in FinTech.",
            situation_analysis="Market analysis showing opportunity.",
            strategy="Strategic positioning framework.",
            pillars=[
                BackendPillar(
                    name="Awareness",
                    description="Build brand recognition",
                    kpi_impact="Impressions +50%"
                ),
                BackendPillar(
                    name="Trust",
                    description="Establish credibility",
                    kpi_impact="Engagement +30%"
                ),
                BackendPillar(
                    name="Conversion",
                    description="Drive signups",
                    kpi_impact="Leads +40%"
                ),
            ]
        )

        # Patch at the point where it's imported (inside the function)
        with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(return_value=mock_marketing_plan)):
            result = await generate_strategy(intake)

        # Verify StrategyDoc structure
        assert isinstance(result, StrategyDoc)
        assert result.brand_name == "Strategy Test Co"
        assert result.industry == "FinTech"
        assert "Test summary" in result.executive_summary
        assert "Market analysis" in result.situation_analysis
        assert "Strategic positioning" in result.strategy_narrative
        assert len(result.pillars) == 3
        assert result.pillars[0].name == "Awareness"
        assert result.pillars[0].kpi_impact == "Impressions +50%"
        assert result.primary_goal == "Drive awareness"
        assert result.timeline == "6 months"

    @pytest.mark.asyncio
    async def test_strategy_doc_from_existing_response(self):
        """StrategyDoc.from_existing_response() adapter works."""
        legacy_response = {
            "brand_name": "Legacy Co",
            "industry": "Retail",
            "executive_summary": "Legacy summary",
            "situation_analysis": "Legacy analysis",
            "strategy": "Legacy strategy",
            "pillars": [
                {"name": "P1", "description": "D1", "kpi_impact": "K1"},
                {"name": "P2", "description": "D2", "kpi_impact": "K2"},
            ],
            "primary_goal": "Growth",
            "timeline": "Q2"
        }

        doc = StrategyDoc.from_existing_response(legacy_response)

        assert doc.brand_name == "Legacy Co"
        assert doc.industry == "Retail"
        assert doc.executive_summary == "Legacy summary"
        assert len(doc.pillars) == 2
        assert doc.pillars[0].name == "P1"
        assert doc.primary_goal == "Growth"

    def test_no_backend_imports_strategy_domain_models(self):
        """Backend code should not import from aicmo.domain.strategy yet."""
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "-E", r"from aicmo\.domain\.strategy|from aicmo\.strategy", "backend/", "--exclude-dir=tests"],
            capture_output=True,
            text=True
        )
        # Should return non-zero (no matches) since backend doesn't use new models yet
        assert result.returncode != 0, "Backend should not import aicmo.domain.strategy yet (Phase 1 isolation)"
