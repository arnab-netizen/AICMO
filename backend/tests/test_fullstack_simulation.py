"""End-to-end fullstack simulation tests for AICMO core flows."""

import json
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _assert_no_stub_strings(obj):
    """Assert that response doesn't contain placeholder/stub markers."""
    blob = json.dumps(obj).lower()
    for marker in ["todo", "stub", "lorem ipsum", "sample only", "dummy"]:
        assert marker not in blob, f"Stub marker '{marker}' found in response"


def test_health_endpoint_exists():
    """Verify health endpoint is accessible."""
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"


def test_aicmo_generate_endpoint_accessible():
    """
    Test that /aicmo/generate endpoint is accessible and returns
    a valid AICMOOutputReport structure without stub content.
    """
    from aicmo.io.client_reports import (
        ClientInputBrief,
        BrandBrief,
        AudienceBrief,
        GoalBrief,
        VoiceBrief,
        ProductServiceBrief,
        AssetsConstraintsBrief,
        OperationsBrief,
        StrategyExtrasBrief,
    )

    brief = ClientInputBrief(
        brand=BrandBrief(
            brand_name="SimBrand",
            industry="SaaS",
            business_type="B2B",
            description="Simulation testing tool",
        ),
        audience=AudienceBrief(
            primary_customer="QA engineers",
            pain_points=["Testing complexity", "Time to market"],
        ),
        goal=GoalBrief(
            primary_goal="Increase adoption",
            timeline="6 months",
        ),
        voice=VoiceBrief(tone_of_voice=["professional", "clear"]),
        product_service=ProductServiceBrief(items=[]),
        assets_constraints=AssetsConstraintsBrief(focus_platforms=["LinkedIn"]),
        operations=OperationsBrief(needs_calendar=True),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["reliable", "innovative"],
            success_30_days="Increase engagement 20%",
        ),
    )

    payload = {
        "brief": brief.model_dump(),
        "generate_marketing_plan": True,
        "generate_campaign_blueprint": True,
        "generate_social_calendar": True,
        "generate_performance_review": False,
        "generate_creatives": True,
        "industry_key": "b2b_saas",  # Phase 5: Test industry preset
    }

    resp = client.post("/aicmo/generate", json=payload)
    assert resp.status_code == 200, f"Generate failed: {resp.status_code}\n{resp.text}"

    data = resp.json()

    # Verify basic structure
    assert "marketing_plan" in data
    assert "campaign_blueprint" in data
    assert "social_calendar" in data
    assert "creatives" in data

    # Verify no stub content
    _assert_no_stub_strings(data)


def test_aicmo_industries_endpoint_returns_presets():
    """
    Test that /aicmo/industries endpoint lists available industry presets.
    """
    resp = client.get("/aicmo/industries")
    assert resp.status_code == 200, f"Industries endpoint failed: {resp.status_code}"

    data = resp.json()
    assert "industries" in data
    assert isinstance(data["industries"], list)

    # Verify Phase 5 presets are available
    expected = {"b2b_saas", "ecom_d2c", "local_service", "coaching"}
    actual = set(data["industries"])
    assert expected == actual, f"Expected {expected}, got {actual}"


def test_aicmo_generate_with_no_industry_key_still_works():
    """
    Test that /aicmo/generate works even without industry_key (backward compatible).
    """
    from aicmo.io.client_reports import (
        ClientInputBrief,
        BrandBrief,
        AudienceBrief,
        GoalBrief,
        VoiceBrief,
        ProductServiceBrief,
        AssetsConstraintsBrief,
        OperationsBrief,
        StrategyExtrasBrief,
    )

    brief = ClientInputBrief(
        brand=BrandBrief(
            brand_name="NoPresetBrand",
            industry="Coaching",
            business_type="B2C",
            description="Life coach",
        ),
        audience=AudienceBrief(
            primary_customer="Career changers",
            pain_points=["Uncertainty", "Direction"],
        ),
        goal=GoalBrief(
            primary_goal="Build authority",
            timeline="3 months",
        ),
        voice=VoiceBrief(tone_of_voice=["inspirational", "authentic"]),
        product_service=ProductServiceBrief(items=[]),
        assets_constraints=AssetsConstraintsBrief(focus_platforms=["YouTube", "Instagram"]),
        operations=OperationsBrief(needs_calendar=True),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["empowering", "genuine"],
            success_30_days="Launch first cohort",
        ),
    )

    payload = {
        "brief": brief.model_dump(),
        "generate_marketing_plan": True,
        "generate_campaign_blueprint": True,
        "generate_social_calendar": True,
        "generate_performance_review": False,
        "generate_creatives": True,
        # Omit industry_key to test backward compatibility
    }

    resp = client.post("/aicmo/generate", json=payload)
    assert (
        resp.status_code == 200
    ), f"Generate without industry_key failed: {resp.status_code}\n{resp.text}"

    data = resp.json()
    assert "marketing_plan" in data


def test_aicmo_revise_endpoint_accessible():
    """
    Test that /aicmo/revise endpoint is accessible.
    """
    from aicmo.io.client_reports import ClientInputBrief

    # First generate output
    from aicmo.io.client_reports import (
        BrandBrief,
        AudienceBrief,
        GoalBrief,
        VoiceBrief,
        ProductServiceBrief,
        AssetsConstraintsBrief,
        OperationsBrief,
        StrategyExtrasBrief,
    )

    brief = ClientInputBrief(
        brand=BrandBrief(
            brand_name="ReviseBrand",
            industry="Local Service",
            business_type="B2C",
            description="Beauty salon",
        ),
        audience=AudienceBrief(
            primary_customer="Local customers",
            pain_points=["Visibility", "Bookings"],
        ),
        goal=GoalBrief(
            primary_goal="Increase foot traffic",
            timeline="1 month",
        ),
        voice=VoiceBrief(tone_of_voice=["friendly", "welcoming"]),
        product_service=ProductServiceBrief(items=[]),
        assets_constraints=AssetsConstraintsBrief(focus_platforms=["Instagram", "Google Maps"]),
        operations=OperationsBrief(needs_calendar=True),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["professional", "relaxing"],
            success_30_days="Book 50% more appointments",
        ),
    )

    gen_payload = {
        "brief": brief.model_dump(),
        "generate_marketing_plan": True,
        "generate_campaign_blueprint": False,
        "generate_social_calendar": False,
        "generate_performance_review": False,
        "generate_creatives": False,
    }

    gen_resp = client.post("/aicmo/generate", json=gen_payload)
    assert gen_resp.status_code == 200

    output = gen_resp.json()

    # Now revise
    rev_payload = {
        "brief": brief.model_dump(),
        "current_output": output,
        "instructions": "Make the tone more playful",
    }

    # Using form data as per endpoint signature
    rev_resp = client.post(
        "/aicmo/revise",
        data={
            "meta": json.dumps(rev_payload),
        },
    )
    assert rev_resp.status_code == 200, f"Revise failed: {rev_resp.status_code}\n{rev_resp.text}"

    revised = rev_resp.json()
    assert "marketing_plan" in revised
