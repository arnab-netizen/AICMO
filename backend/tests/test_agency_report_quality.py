import pytest

from backend.agency_report_schema import AgencyReport
from backend.domain_detection import PackDomain
from backend.agency_report_pipeline import (
    assert_agency_grade,
    plan_agency_report_json,
    expand_agency_report_sections,
)
from backend.exceptions import QualityGateFailedError
from backend.genericity_scoring import section_quality_score


def test_agency_report_quality_gate_rejects_placeholder_and_saas():
    bad = AgencyReport(
        brand_name="Demo Brand",
        industry="Automotive",
        primary_goal="Increase qualified leads",
        target_audience="ideal customers",
        positioning_summary="Generic positioning.",
        executive_summary=(
            "This mentions ProductHunt, MRR and ideal customers again. This should fail the quality gate."
        ),
        situation_analysis="Very generic situation analysis.",
        key_insights="Generic insights.",
        strategy="Random SaaS style go-to-market plan.",
        strategic_pillars=["Random pillar"],
        messaging_pyramid="Generic messaging pyramid.",
        campaign_big_idea="Big idea but uses SaaS trial language.",
        campaign_concepts=["Random concept"],
        content_calendar_summary="Totally generic calendar summary.",
        content_calendar_table_markdown=".",
        kpi_framework="Focus on MRR and churn.",
        measurement_plan="Measure ProductHunt launch and G2 reviews.",
        next_30_days_action_plan="Generic plan without dealership context.",
    )

    with pytest.raises(QualityGateFailedError):
        assert_agency_grade(bad, PackDomain.AUTOMOTIVE_DEALERSHIP)


def test_executive_summary_backfill_has_no_placeholders_for_automotive():
    """Ensure deterministic backfill never emits placeholder patterns."""
    brief = {
        "brand_name": "Luxotica Automobiles",
        "industry": "Automotive",
        "primary_goal": "Increase qualified leads and showroom visits for luxury cars",
        "city": "Kolkata",
    }
    domain = PackDomain.AUTOMOTIVE_DEALERSHIP

    plan = plan_agency_report_json(brief=brief, domain=domain)
    report = expand_agency_report_sections(plan, brief, domain)

    # Check executive_summary specifically
    score = section_quality_score(report.executive_summary, domain)
    assert (
        score.scores.get("placeholders", 0) == 0
    ), f"executive_summary contains placeholder patterns: {score.reasons}"

    # Also verify target_audience (another field we backfill)
    score_ta = section_quality_score(report.target_audience, domain)
    assert (
        score_ta.scores.get("placeholders", 0) == 0
    ), f"target_audience contains placeholder patterns: {score_ta.reasons}"
