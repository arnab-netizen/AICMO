"""Real payload fixtures extracted from backend tests - Option B results."""

import json
from aicmo.io.client_reports import (
    ClientInputBrief,
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


def get_minimal_brief() -> ClientInputBrief:
    """Real fixture from test_aicmo_generate_stub_mode.py - Minimal valid brief."""
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


def get_fullstack_brief() -> ClientInputBrief:
    """Real fixture from test_fullstack_simulation.py - More detailed brief."""
    return ClientInputBrief(
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


def get_techflow_brief() -> ClientInputBrief:
    """Real fixture from test_social_calendar_generation.py - Tech flow example."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="TechFlow",
            industry="Software",
            business_type="B2B SaaS",
            description="Workflow automation for teams",
        ),
        audience=AudienceBrief(
            primary_customer="Software teams",
            pain_points=["Time management", "Collaboration overhead"],
        ),
        goal=GoalBrief(
            primary_goal="Increase platform adoption",
            timeline="6 months",
            kpis=["Sign-ups", "Engagement"],
        ),
        voice=VoiceBrief(tone_of_voice=["Professional", "Friendly"]),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="Core Platform",
                    usp="AI-powered workflow optimization",
                )
            ]
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["LinkedIn", "Twitter"],
        ),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


def get_generate_request_payload(brief: ClientInputBrief = None) -> dict:
    """
    Create a full GenerateRequest payload with real brief.

    Args:
        brief: ClientInputBrief instance (defaults to minimal brief)

    Returns:
        Dictionary ready for POST /aicmo/generate endpoint
    """
    if brief is None:
        brief = get_minimal_brief()

    return {
        "brief": brief.model_dump(),
        "generate_marketing_plan": True,
        "generate_campaign_blueprint": True,
        "generate_social_calendar": True,
        "generate_performance_review": False,
        "generate_creatives": True,
    }


def get_payload_json_str(brief: ClientInputBrief = None) -> str:
    """Get JSON string representation of payload (for curl)."""
    return json.dumps(get_generate_request_payload(brief), indent=2)


if __name__ == "__main__":
    # Test payloads
    print("=" * 80)
    print("PAYLOAD 1: Minimal Brief")
    print("=" * 80)
    payload1 = get_generate_request_payload(get_minimal_brief())
    print(json.dumps(payload1, indent=2))

    print("\n" + "=" * 80)
    print("PAYLOAD 2: Fullstack Brief")
    print("=" * 80)
    payload2 = get_generate_request_payload(get_fullstack_brief())
    print(json.dumps(payload2, indent=2))

    print("\n" + "=" * 80)
    print("PAYLOAD 3: TechFlow Brief")
    print("=" * 80)
    payload3 = get_generate_request_payload(get_techflow_brief())
    print(json.dumps(payload3, indent=2))
