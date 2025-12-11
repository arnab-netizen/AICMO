"""
Self-Test Engine Test Inputs

Synthetic briefs and scenarios for end-to-end testing.
Uses real ClientInputBrief schema from aicmo.io.client_reports.
"""

from typing import Dict, List, Optional
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


# ============================================================================
# CRITICAL GENERATORS - Must have schema-correct briefs
# ============================================================================

CRITICAL_GENERATOR_NAMES = {
    "persona_generator",
    "social_calendar_generator",
    "situation_analysis_generator",
    "messaging_pillars_generator",
    "swot_generator",
}

CRITICAL_PACKAGER_NAMES = {
    "generate_full_deck_pptx",
    "generate_html_summary",
    "generate_strategy_pdf",
}

# ============================================================================
# SCHEMA-CORRECT BRIEFS (using actual ClientInputBrief structure)
# ============================================================================


def _saas_startup_brief() -> ClientInputBrief:
    """SaaS startup brief - schema-correct for all generators."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="CloudSync AI",
            industry="SaaS",
            product_service="Cloud-based data synchronization platform using AI",
            primary_goal="Increase brand awareness and generate qualified leads",
            primary_customer="Enterprise data teams",
            secondary_customer="Operations managers",
            brand_tone="Technical yet approachable",
            location="US",
            timeline="6 months",
            competitors=["Fivetran", "Informatica"],
        ),
        audience=AudienceBrief(
            primary_customer="Enterprise data teams",
            secondary_customer="Operations managers",
            pain_points=["Manual data sync causes delays", "Error-prone manual processes"],
            online_hangouts=["LinkedIn", "Twitter", "Industry forums"],
        ),
        goal=GoalBrief(
            primary_goal="Generate 200 qualified leads per quarter",
            secondary_goal="Establish thought leadership in data automation",
            timeline="6 months",
            kpis=["Lead volume", "Lead quality", "Website traffic"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["Technical", "Authoritative", "Helpful"],
            has_guidelines=False,
            preferred_colors="Blue and white",
        ),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="CloudSync AI Platform",
                    usp="AI-powered data sync with 99.9% accuracy",
                    pricing_note="Enterprise pricing model",
                )
            ],
            testimonials_or_proof="Used by 50+ enterprises",
        ),
        assets_constraints=AssetsConstraintsBrief(
            already_posting=True,
            focus_platforms=["LinkedIn", "Twitter"],
            constraints=["Limited content production capacity"],
            budget="$50k-100k quarterly",
        ),
        operations=OperationsBrief(
            approval_frequency="Weekly",
            needs_calendar=True,
            wants_posting_and_scheduling=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["Innovative", "Reliable", "Efficient"],
            success_30_days="20 qualified leads and 500 website sessions",
            must_include_messages="AI-powered, Enterprise-grade",
            tagline="Automate your data flow",
        ),
    )


def _restaurant_brief() -> ClientInputBrief:
    """Restaurant brief - local business, schema-correct."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="The Harvest Table",
            industry="Food & Beverage",
            product_service="Farm-to-table restaurant with seasonal menus",
            primary_goal="Fill tables with quality guests",
            primary_customer="Health-conscious foodies",
            secondary_customer="Local families",
            brand_tone="Warm and inviting",
            location="Portland, OR",
            timeline="Q1 2025",
        ),
        audience=AudienceBrief(
            primary_customer="Health-conscious foodies",
            secondary_customer="Local families",
            pain_points=["Hard to find restaurants aligned with values"],
            online_hangouts=["Instagram", "Facebook", "Google Reviews"],
        ),
        goal=GoalBrief(
            primary_goal="Increase table reservations by 30%",
            secondary_goal="Build loyal customer community",
            timeline="Q1 2025",
            kpis=["Reservations", "Reviews", "Instagram followers"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["Warm", "Authentic", "Educational"],
            has_guidelines=False,
            preferred_colors="Green and earth tones",
        ),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="Seasonal Farm-to-Table Dining",
                    usp="Local ingredients sourced weekly",
                )
            ],
            current_offers="Happy hour 4-6pm weekdays",
        ),
        assets_constraints=AssetsConstraintsBrief(
            already_posting=True,
            focus_platforms=["Instagram", "Facebook"],
            content_that_worked="Beautiful food photography",
        ),
        operations=OperationsBrief(
            approval_frequency="Daily",
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["Authentic", "Local", "Wholesome"],
            success_30_days="10 new reservations from social",
        ),
    )


def _fashion_brief() -> ClientInputBrief:
    """Fashion brand brief - DTC, schema-correct."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="EcoThread Co",
            industry="Fashion & Apparel",
            product_service="Sustainable clothing from recycled materials",
            primary_goal="Increase online sales",
            primary_customer="Eco-conscious millennials",
            secondary_customer="Gen Z consumers",
            brand_tone="Trendy and authentic",
            location="US",
            timeline="Q1 2025",
        ),
        audience=AudienceBrief(
            primary_customer="Eco-conscious millennials",
            secondary_customer="Gen Z consumers",
            pain_points=["Conflicting sustainability and style"],
            online_hangouts=["TikTok", "Instagram", "Pinterest"],
        ),
        goal=GoalBrief(
            primary_goal="Increase monthly online sales 25%",
            secondary_goal="Build community of sustainability advocates",
            timeline="Q1 2025",
            kpis=["Sales", "ROAS", "Community engagement"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["Trendy", "Passionate", "Relatable"],
            has_guidelines=False,
            preferred_colors="Earthy tones",
        ),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="Sustainable Apparel Collection",
                    usp="100% recycled materials, stylish designs",
                    pricing_note="Premium pricing reflecting sustainability",
                )
            ],
            testimonials_or_proof="1000+ 5-star reviews",
        ),
        assets_constraints=AssetsConstraintsBrief(
            already_posting=True,
            focus_platforms=["TikTok", "Instagram"],
            content_that_worked="User-generated content",
        ),
        operations=OperationsBrief(
            approval_frequency="Weekly",
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["Sustainable", "Trendy", "Authentic"],
            success_30_days="$10k in additional sales",
        ),
    )


# ============================================================================
# MINIMAL BRIEFS (for optional/non-critical generators)
# ============================================================================


def _minimal_brief() -> ClientInputBrief:
    """Minimal brief with all required fields only."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="Test Brand",
            industry="Technology",
            product_service="Test product",
            primary_goal="Test goal",
            primary_customer="Test customer",
        ),
        audience=AudienceBrief(
            primary_customer="Test customer",
        ),
        goal=GoalBrief(
            primary_goal="Test goal",
        ),
        voice=VoiceBrief(),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


# ============================================================================
# SCENARIO MAPPING - Maps generator names to appropriate briefs
# ============================================================================

TEST_SCENARIOS_BY_GENERATOR = {
    "persona_generator": [_saas_startup_brief(), _restaurant_brief()],
    "social_calendar_generator": [_saas_startup_brief(), _fashion_brief()],
    "situation_analysis_generator": [_saas_startup_brief()],
    "messaging_pillars_generator": [_restaurant_brief()],
    "swot_generator": [_fashion_brief()],
    "agency_grade_processor": [_minimal_brief()],
    "output_formatter": [_minimal_brief()],
}


# ============================================================================
# PUBLIC API - Backward compatible access
# ============================================================================


def get_all_test_briefs() -> List[ClientInputBrief]:
    """Get all test briefs."""
    return [
        _saas_startup_brief(),
        _restaurant_brief(),
        _fashion_brief(),
    ]


def get_briefs_for_generator(generator_name: str) -> List[ClientInputBrief]:
    """Get briefs for a specific generator."""
    return TEST_SCENARIOS_BY_GENERATOR.get(generator_name, [_minimal_brief()])


def get_quick_test_briefs(count: int = 2) -> List[ClientInputBrief]:
    """Get a subset of briefs for quick testing."""
    all_briefs = get_all_test_briefs()
    return all_briefs[:count]

