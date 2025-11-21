"""
Test offline stub mode for /aicmo/generate endpoint.

Ensures the endpoint works without LLM enabled (default AICMO_USE_LLM=0).
"""

import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app, GenerateRequest
from aicmo.io.client_reports import (
    ClientInputBrief,
    AICMOOutputReport,
    CreativesBlock,
)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_brief():
    """Minimal valid ClientInputBrief for testing."""
    from aicmo.io.client_reports import (
        BrandBrief,
        AudienceBrief,
        GoalBrief,
        VoiceBrief,
        ProductServiceBrief,
        ProductServiceItem,
        AssetsConstraintsBrief,
        OperationsBrief,
        StrategyExtrasBrief,
    )

    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="TechCorp",
            industry="SaaS",
            business_type="B2B",
            description="Project management software",
        ),
        audience=AudienceBrief(
            primary_customer="Tech-savvy entrepreneurs",
            pain_points=["Workflow inefficiency", "Team coordination"],
        ),
        goal=GoalBrief(
            primary_goal="Launch new SaaS product",
            timeline="3 months",
            kpis=["Lead generation", "Brand awareness"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["Professional", "Approachable"],
        ),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="Main Product",
                    usp="Streamline team workflows",
                )
            ],
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["LinkedIn", "Twitter"],
        ),
        operations=OperationsBrief(
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["Innovative", "Reliable"],
        ),
    )


def test_aicmo_generate_stub_mode_offline(client, sample_brief):
    """Test /aicmo/generate returns valid output in offline stub mode (default)."""
    # Ensure AICMO_USE_LLM is disabled (default)
    os.environ.pop("AICMO_USE_LLM", None)

    req = GenerateRequest(brief=sample_brief)
    payload = req.model_dump(mode="json")

    response = client.post("/aicmo/generate", json=payload)

    assert response.status_code == 200
    data = response.json()
    output = AICMOOutputReport(**data)

    # Validate structure
    assert output.marketing_plan is not None
    assert output.marketing_plan.executive_summary
    assert output.marketing_plan.situation_analysis
    assert output.marketing_plan.strategy

    assert output.campaign_blueprint is not None
    assert output.campaign_blueprint.big_idea

    assert output.social_calendar is not None
    assert isinstance(output.social_calendar, list)
    assert len(output.social_calendar) > 0

    assert output.persona_cards is not None
    assert isinstance(output.persona_cards, list)
    assert len(output.persona_cards) > 0

    assert output.action_plan is not None
    assert output.action_plan.immediate_actions
    assert output.action_plan.month_2_3_actions
    assert output.action_plan.month_4_6_actions

    # Validate creatives if present
    if output.creatives:
        assert isinstance(output.creatives, CreativesBlock)
        assert output.creatives.hooks
        assert output.creatives.captions
        assert output.creatives.email_subject_lines


def test_aicmo_generate_deterministic_when_llm_disabled(client, sample_brief):
    """Test /aicmo/generate is deterministic when LLM is disabled."""
    os.environ["AICMO_USE_LLM"] = "0"

    req = GenerateRequest(brief=sample_brief)
    payload = req.model_dump(mode="json")

    # Call twice
    response1 = client.post("/aicmo/generate", json=payload)
    response2 = client.post("/aicmo/generate", json=payload)

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    # With stub mode, outputs should be identical (deterministic)
    # Note: Creatives use random sampling, so they may differ;
    # but marketing_plan fields should be identical.
    assert (
        data1["marketing_plan"]["executive_summary"] == data2["marketing_plan"]["executive_summary"]
    )
    assert data1["campaign_blueprint"]["big_idea"] == data2["campaign_blueprint"]["big_idea"]


def test_aicmo_generate_with_llm_env_disabled_explicitly(client, sample_brief):
    """Test /aicmo/generate with AICMO_USE_LLM explicitly set to '0'."""
    os.environ["AICMO_USE_LLM"] = "0"

    req = GenerateRequest(brief=sample_brief)
    payload = req.model_dump(mode="json")

    response = client.post("/aicmo/generate", json=payload)

    assert response.status_code == 200
    data = response.json()
    output = AICMOOutputReport(**data)

    # Should have all expected fields
    assert output.marketing_plan
    assert output.campaign_blueprint
    assert output.social_calendar
    assert output.persona_cards
    assert output.action_plan
