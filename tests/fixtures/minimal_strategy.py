"""
Minimal valid Strategy Contract fixture for testing.

This fixture provides the SMALLEST structurally valid Strategy Contract
that passes schema validation.

Schema validation enforces ONLY:
- All 8 layers exist
- All required fields exist
- Fields are non-empty strings

Quality/completeness/richness enforcement happens in QC rules, NOT here.
"""

from typing import Dict, Any


def minimal_strategy_contract() -> Dict[str, Any]:
    """
    Returns minimal structurally valid Strategy Contract.
    
    This contract:
    - WILL pass schema validation (structure is valid)
    - WILL fail QC rules (content is minimal, not agency-grade)
    
    This separation is intentional:
    - Schema validation checks structure
    - QC rules check quality
    """
    return {
        "schema_version": "strategy_contract_v1",
        
        # Layer 1: Business Reality Alignment
        "layer1_business_reality": {
            "business_model_summary": "B2B SaaS",
            "revenue_streams": "Subscriptions",
            "unit_economics": "CAC $500, LTV $5000",
            "pricing_logic": "Value-based pricing",
            "growth_constraint": "Product-market fit",
            "bottleneck": "Awareness"
        },
        
        # Layer 2: Market & Competitive Truth
        "layer2_market_truth": {
            "category_maturity": "Growth",
            "white_space_logic": "Mid-market underserved",
            "what_not_to_do": "Don't compete on price"
        },
        
        # Layer 3: Audience Decision Psychology
        "layer3_audience_psychology": {
            "awareness_state": "Problem-aware",
            "objection_hierarchy": "Price, implementation",
            "trust_transfer_mechanism": "Case studies and testimonials"
        },
        
        # Layer 4: Value Proposition Architecture
        "layer4_value_architecture": {
            "core_promise": "Reduce costs 30%",
            "sacrifice_framing": "We focus on SME, not enterprise",
            "differentiation_logic": "Structural"
        },
        
        # Layer 5: Strategic Narrative
        "layer5_narrative": {
            "narrative_problem": "Manual processes slow growth",
            "narrative_tension": "Competitors are automating faster",
            "narrative_resolution": "Automation unlocks scale",
            "enemy_definition": "Manual work and inefficiency",
            "repetition_logic": "Automation saves time and reduces errors"
        },
        
        # Layer 6: Channel Strategy
        "layer6_channel_strategy": {
            "channels": [
                {"name": "LinkedIn", "strategic_role": "Awareness"}
            ]
        },
        
        # Layer 7: Execution Constraints
        "layer7_constraints": {
            "tone_boundaries": "Professional",
            "forbidden_language": "No hype or exaggeration",
            "claim_boundaries": "Only measurable claims",
            "compliance_rules": "GDPR compliant"
        },
        
        # Layer 8: Measurement & Learning Loop
        "layer8_measurement": {
            "success_definition": "100 leads/month",
            "leading_indicators": "Engagement rate",
            "lagging_indicators": "Lead volume",
            "decision_rules": "If CAC > $1000, pause"
        }
    }
