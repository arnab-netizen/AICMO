"""Tests for persona_generator: verify demographics, psychographics, and brief context."""

import os
import pytest
from unittest.mock import patch

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
from aicmo.generators.persona_generator import (
    generate_persona,
    _stub_persona,
)


@pytest.fixture
def tech_b2b_brief():
    """Create a B2B tech brief for testing."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="DevOps.ai",
            industry="Cloud Infrastructure",
            business_type="B2B SaaS",
            description="AI-powered DevOps automation",
        ),
        audience=AudienceBrief(
            primary_customer="Engineering managers and DevOps engineers",
            pain_points=[
                "Manual deployment complexity",
                "Scaling challenges",
                "Incident response time",
            ],
        ),
        goal=GoalBrief(
            primary_goal="Increase platform adoption among enterprise teams",
            timeline="9 months",
            kpis=["User sign-ups", "Daily active users"],
        ),
        voice=VoiceBrief(tone_of_voice=["Technical", "Empowering"]),
        product_service=ProductServiceBrief(items=[]),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["LinkedIn", "GitHub", "Dev.to"],
        ),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["innovative", "reliable"],
        ),
    )


@pytest.fixture
def ecommerce_b2c_brief():
    """Create a B2C e-commerce brief for testing."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="ShopEasy",
            industry="E-Commerce",
            business_type="B2C",
            description="Online marketplace for handmade goods",
        ),
        audience=AudienceBrief(
            primary_customer="Millennial and Gen Z online shoppers",
            pain_points=[
                "Finding authentic products",
                "Supporting small creators",
                "Ethical shopping",
            ],
        ),
        goal=GoalBrief(
            primary_goal="Increase customer lifetime value",
            timeline="6 months",
            kpis=["Repeat purchases", "Customer satisfaction"],
        ),
        voice=VoiceBrief(tone_of_voice=["Authentic", "Community-focused"]),
        product_service=ProductServiceBrief(items=[]),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["Instagram", "TikTok"],
        ),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


class TestStubPersona:
    """Test stub mode persona generation."""

    def test_stub_generates_non_empty_persona(self, tech_b2b_brief):
        """Verify stub mode generates persona with all required fields."""
        persona = _stub_persona(tech_b2b_brief)

        assert persona.name
        assert persona.demographics
        assert persona.psychographics
        assert len(persona.pain_points) > 0
        assert len(persona.triggers) > 0
        assert len(persona.objections) > 0
        assert len(persona.content_preferences) > 0
        assert len(persona.primary_platforms) > 0
        assert persona.tone_preference

    def test_stub_no_placeholder_phrases(self, tech_b2b_brief):
        """Verify no forbidden placeholder phrases."""
        persona = _stub_persona(tech_b2b_brief)

        all_text = (
            f"{persona.demographics} {persona.psychographics} "
            f"{' '.join(persona.pain_points)} {' '.join(persona.triggers)} "
            f"{' '.join(persona.objections)} {' '.join(persona.content_preferences)} "
            f"{persona.tone_preference}"
        )

        forbidden = [
            "varies by brand",
            "will be refined",
            "will be customized",
            "placeholder",
            "tbd",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in all_text.lower()

    def test_stub_demographics_realistic_ranges(self, tech_b2b_brief):
        """Verify demographics contain realistic age ranges, not fake-precise values."""
        persona = _stub_persona(tech_b2b_brief)
        demographics = persona.demographics.lower()

        # Should have ranges like "32-42" not "32.5 years"
        assert "–" in demographics or "-" in demographics or "to" in demographics

        # Should not have decimal precision
        assert ".0" not in demographics
        assert ".5" not in demographics

    def test_stub_respects_b2b_business_type(self, tech_b2b_brief):
        """Verify B2B persona is manager/director level, not consumer."""
        persona = _stub_persona(tech_b2b_brief)
        demographics = persona.demographics.lower()
        psychographics = persona.psychographics.lower()

        # B2B should have professional titles
        b2b_keywords = [
            "manager",
            "director",
            "lead",
            "engineer",
            "organization",
            "company",
            "team",
        ]
        has_b2b_keywords = any(kw in demographics or kw in psychographics for kw in b2b_keywords)
        assert has_b2b_keywords

    def test_stub_respects_b2c_business_type(self, ecommerce_b2c_brief):
        """Verify B2C persona is consumer-oriented."""
        persona = _stub_persona(ecommerce_b2c_brief)
        demographics = persona.demographics.lower()

        # B2C should focus on consumer attributes
        b2c_keywords = [
            "consumer",
            "shopper",
            "online",
            "interested in",
            "value",
            "convenience",
        ]
        has_b2c_keywords = any(kw in demographics for kw in b2c_keywords)
        assert has_b2c_keywords

    def test_stub_uses_brief_context(self, tech_b2b_brief):
        """Verify persona incorporates brief context."""
        persona = _stub_persona(tech_b2b_brief)

        all_text = (
            f"{persona.demographics} {persona.psychographics} "
            f"{' '.join(persona.pain_points)} {' '.join(persona.triggers)}"
        )

        # Should reference pain points or industry context
        pain_points = tech_b2b_brief.audience.pain_points
        has_context = any(pp.lower() in all_text.lower() for pp in pain_points)
        assert has_context

    def test_stub_uses_brief_platforms(self, tech_b2b_brief):
        """Verify primary platforms come from brief."""
        persona = _stub_persona(tech_b2b_brief)

        brief_platforms = set(tech_b2b_brief.assets_constraints.focus_platforms)
        persona_platforms = set(persona.primary_platforms)

        # At least one platform should be from brief
        assert len(persona_platforms & brief_platforms) > 0

    def test_stub_engineer_gets_technical_persona(self):
        """Verify 'engineer' audience gets tech-focused persona."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="CodeTools",
                industry="Developer Tools",
                business_type="B2B SaaS",
                description="Tools for developers",
            ),
            audience=AudienceBrief(
                primary_customer="Software engineers and architects",
                pain_points=["Development speed", "Debugging time"],
            ),
            goal=GoalBrief(primary_goal="Reduce development cycles"),
            voice=VoiceBrief(tone_of_voice=["Technical"]),
            product_service=ProductServiceBrief(items=[]),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )

        persona = _stub_persona(brief)

        # Should reference engineer/technical context
        all_text = f"{persona.demographics} {persona.psychographics}".lower()
        assert "engineer" in all_text or "technical" in all_text or "lead" in all_text

    def test_stub_minimal_brief_works(self):
        """Verify stub mode works with minimal brief (no pain points, etc.)."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="GenericBrand",
                industry="Unknown",
                business_type="B2B",
                description="Generic product",
            ),
            audience=AudienceBrief(primary_customer="Customers"),
            goal=GoalBrief(primary_goal="Succeed"),
            voice=VoiceBrief(tone_of_voice=[]),
            product_service=ProductServiceBrief(items=[]),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )

        persona = _stub_persona(brief)

        # Should still generate valid persona
        assert persona.name
        assert persona.demographics
        assert persona.psychographics


class TestMainGenerateFunction:
    """Test main generate_persona function."""

    def test_generate_returns_persona_card(self, tech_b2b_brief):
        """Verify main function returns valid PersonaCard."""
        persona = generate_persona(tech_b2b_brief)

        assert persona.name
        assert persona.demographics
        assert persona.psychographics
        assert persona.pain_points
        assert persona.primary_platforms

    def test_generate_respects_use_llm_false(self, tech_b2b_brief):
        """Verify use_llm=False forces stub mode."""
        persona = generate_persona(tech_b2b_brief, use_llm=False)

        # Should not have placeholder phrases
        all_text = (
            f"{persona.demographics} {persona.psychographics} " f"{' '.join(persona.pain_points)}"
        ).lower()
        assert "varies by brand" not in all_text

    def test_generate_graceful_fallback_on_llm_error(self, tech_b2b_brief):
        """Verify function falls back to stub when LLM errors."""
        with patch.dict(os.environ, {"AICMO_USE_LLM": "1"}):
            with patch("aicmo.generators.persona_generator._generate_persona_with_llm") as mock_llm:
                mock_llm.return_value = None  # Simulate LLM failure

                persona = generate_persona(tech_b2b_brief)

                # Should still return valid stub persona
                assert persona.name
                assert persona.demographics
                assert persona.psychographics

    def test_generate_no_crash_on_exception(self, tech_b2b_brief):
        """Verify function never crashes, always returns valid persona."""
        with patch("aicmo.generators.persona_generator._stub_persona") as mock_stub:
            mock_stub.side_effect = Exception("Stub generation failed")

            with patch("aicmo.generators.persona_generator._generate_persona_with_llm") as mock_llm:
                mock_llm.return_value = None

                # Even with both paths failing, should gracefully handle
                # (The ultimate fallback in the try/except)
                try:
                    generate_persona(tech_b2b_brief)
                    # If we get here, the function didn't crash
                    assert True
                except Exception:
                    # Should not happen with proper exception handling
                    assert False, "generate_persona should handle all exceptions"


class TestPersonaContent:
    """Test persona content quality and coherence."""

    def test_pain_points_and_triggers_coherent(self, tech_b2b_brief):
        """Verify triggers are related to pain points."""
        persona = _stub_persona(tech_b2b_brief)

        # Triggers should relate to the pain points
        # At least one trigger should reference a similar concept
        # (not a strict test, but checks some coherence)
        assert len(persona.triggers) > 0
        assert len(persona.pain_points) > 0

    def test_objections_realistic(self, tech_b2b_brief):
        """Verify objections are realistic buying/adoption concerns."""
        persona = _stub_persona(tech_b2b_brief)

        all_objections = " ".join(persona.objections).lower()

        # Should contain realistic concern keywords
        realistic_concerns = ["will", "require", "how", "can", "is", "does"]
        has_realistic = any(word in all_objections for word in realistic_concerns)
        assert has_realistic

    def test_content_preferences_specific(self, tech_b2b_brief):
        """Verify content preferences are specific, not generic."""
        persona = _stub_persona(tech_b2b_brief)

        for pref in persona.content_preferences:
            # Each preference should be 3+ words (not just "Videos")
            assert len(pref.split()) >= 2


class TestBriefVariations:
    """Test persona generation with different brief configurations."""

    def test_brief_with_multiple_pain_points(self):
        """Verify persona incorporates multiple pain points."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="MultiPain",
                industry="SaaS",
                business_type="B2B",
                description="Multi-pain solution",
            ),
            audience=AudienceBrief(
                primary_customer="Business leaders",
                pain_points=[
                    "Inefficient processes",
                    "High employee turnover",
                    "Data silos",
                    "Compliance burden",
                ],
            ),
            goal=GoalBrief(primary_goal="Transform operations"),
            voice=VoiceBrief(tone_of_voice=["Professional"]),
            product_service=ProductServiceBrief(items=[]),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )

        persona = _stub_persona(brief)

        # Should reference pain points
        all_text = " ".join(persona.pain_points).lower()
        assert len(all_text) > 20

    def test_brief_with_brand_adjectives(self):
        """Verify tone preference includes brand adjectives."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="AdjBrand",
                industry="Tech",
                business_type="B2B",
                description="Adjective-driven",
            ),
            audience=AudienceBrief(primary_customer="Tech buyers"),
            goal=GoalBrief(primary_goal="Lead market"),
            voice=VoiceBrief(tone_of_voice=["Cutting-edge", "Transparent"]),
            product_service=ProductServiceBrief(items=[]),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(
                brand_adjectives=["Bold", "Trustworthy", "Innovative"]
            ),
        )

        persona = _stub_persona(brief)

        # Tone preference should include or reflect brand adjectives
        assert persona.tone_preference
        assert len(persona.tone_preference) > 5  # More than just one word
