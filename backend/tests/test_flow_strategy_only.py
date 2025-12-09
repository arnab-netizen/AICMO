"""
Flow Test: Strategy-only generation

Tests that strategy generation works end-to-end with validation.
"""

import pytest
from aicmo.domain.intake import ClientIntake
from aicmo.strategy.service import generate_strategy


@pytest.mark.asyncio
async def test_strategy_only_flow():
    """
    G2: Test strategy-only flow through real service.
    
    Verifies:
    - Strategy generation completes
    - validate_strategy_doc passes
    - No placeholder text in outputs
    """
    # Create realistic client intake
    intake = ClientIntake(
        brand_name="TechInnovate Corp",
        industry="Technology",
        primary_goal="Increase brand awareness and generate qualified B2B leads",
        target_audiences=["CTOs and IT Directors at mid-size companies"],
        timeline="Q1 2025",
        constraints="Budget: $50k, Focus on digital channels only"
    )
    
    # Generate strategy through real service (includes validation)
    strategy_doc = await generate_strategy(intake)
    
    # Basic assertions
    assert strategy_doc is not None
    assert strategy_doc.brand_name == "TechInnovate Corp"
    assert len(strategy_doc.executive_summary) > 50
    assert len(strategy_doc.objectives) > 0
    assert len(strategy_doc.key_messages) > 0
    assert len(strategy_doc.pillars) > 0
    
    # Verify no placeholders (validation should have caught this)
    assert "TBD" not in strategy_doc.executive_summary
    assert "Not specified" not in strategy_doc.executive_summary
    assert "lorem ipsum" not in strategy_doc.executive_summary.lower()
    
    # Check pillars have meaningful content
    for pillar in strategy_doc.pillars:
        assert len(pillar.name) > 0
        assert len(pillar.description) > 0


@pytest.mark.asyncio
async def test_strategy_generation_with_kaizen():
    """
    G2: Test strategy generation with Kaizen context.
    
    Verifies that Kaizen-influenced strategy still passes validation.
    """
    from aicmo.learning.kaizen_service import KaizenContext
    
    intake = ClientIntake(
        brand_name="FinTech Startup",
        industry="Financial Services",
        primary_goal="Launch product and acquire first 1000 users",
        target_audiences=["Small business owners"],
        timeline="6 months"
    )
    
    # Create Kaizen context with successful patterns
    kaizen = KaizenContext(
        successful_pillars=["Content Marketing", "LinkedIn Outreach"],
        recommended_tones=["Professional", "Trustworthy"],
        confidence=0.8
    )
    
    # Generate with Kaizen influence
    strategy_doc = await generate_strategy(intake, kaizen_context=kaizen)
    
    # Should still pass all validations
    assert strategy_doc is not None
    assert len(strategy_doc.executive_summary) > 50
    assert "TBD" not in strategy_doc.executive_summary
    

@pytest.mark.asyncio
async def test_strategy_validation_catches_issues():
    """
    G2: Verify that validation catches problematic strategy outputs.
    
    This tests the contracts layer by attempting to validate bad data.
    """
    from aicmo.domain.strategy import StrategyDoc, StrategyPillar
    from aicmo.core.contracts import validate_strategy_doc
    
    # Create strategy with placeholder text (should fail validation)
    bad_strategy = StrategyDoc(
        brand_name="Test",
        industry="Tech",
        executive_summary="TBD - need to write this later" + " " * 50,  # Make it long enough
        situation_analysis="Analysis",
        strategy_narrative="Strategy",
        pillars=[StrategyPillar(name="Digital", description="Desc", kpi_impact="Impact")],
        objectives=["Obj1"],
        key_messages=["Msg1"],
        primary_goal="Growth",
        timeline="Q1"
    )
    
    # Validation should catch the "TBD" placeholder
    with pytest.raises(ValueError, match="placeholder"):
        validate_strategy_doc(bad_strategy)
