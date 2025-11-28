"""Regression test: GenerateRequest must have generate_personas attribute."""
import pytest
from backend.main import GenerateRequest
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


@pytest.fixture
def sample_brief():
    """Minimal valid ClientInputBrief for testing."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="TechCorp",
            industry="SaaS",
            product_service="Project management software",
            primary_goal="Launch new SaaS product",
            primary_customer="Tech-savvy entrepreneurs",
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


def test_generate_request_has_generate_personas_attribute(sample_brief):
    """Regression test: GenerateRequest must have generate_personas attribute."""
    req = GenerateRequest(
        brief=sample_brief,
        generate_personas=True,
    )
    
    assert hasattr(req, "generate_personas")
    assert isinstance(req.generate_personas, bool)
    assert req.generate_personas is True


def test_generate_request_generate_personas_defaults_to_true(sample_brief):
    """Regression test: generate_personas should default to True."""
    req = GenerateRequest(brief=sample_brief)
    
    assert req.generate_personas is True, "generate_personas should default to True"


def test_generate_request_generate_personas_can_be_false(sample_brief):
    """Regression test: generate_personas can be explicitly set to False."""
    req = GenerateRequest(
        brief=sample_brief,
        generate_personas=False,
    )
    
    assert req.generate_personas is False, "generate_personas should be False when set explicitly"
