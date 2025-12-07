import pytest

from backend.agency_report_schema import AgencyReport
from backend.pdf_renderer import render_agency_report_pdf, WEASYPRINT_AVAILABLE
from backend.exceptions import BlankPdfError

TEMPLATE_NAME = "campaign_strategy.html"


def _fake_report() -> AgencyReport:
    return AgencyReport(
        brand_name="Luxotica Automobiles",
        industry="Automotive",
        primary_goal="Increase qualified leads and showroom visits for luxury cars",
        target_audience="Affluent car buyers in Kolkata",
        positioning_summary="Boutique luxury dealership focused on curated premium vehicles.",
        executive_summary=(
            "Short exec summary for testing with enough content to render robustly. "
            "Discusses local market dynamics, consumer preferences, and positioning."
        ),
        situation_analysis=(
            "Brief situation analysis about the local luxury automotive market, competition, and buyer behavior."
        ),
        key_insights=(
            "Key insights include: seasonal demand spikes, financing preferences, and concierge expectations."
        ),
        strategy=(
            "High-level strategy tailored to automotive dealerships covering search, social proof, and showroom experiences."
        ),
        strategic_pillars=[
            "Own the local luxury search terms.",
            "Build showroom as an experience hub.",
            "Leverage social proof from existing customers.",
        ],
        messaging_pyramid="Simple messaging pyramid for PDF test with value, proof, and CTA layers.",
        campaign_big_idea="Where Kolkata discovers its next luxury drive.",
        campaign_concepts=[
            "Weekend test-drive experiences.",
            "Owner spotlight series.",
        ],
        content_calendar_summary=(
            "One paragraph summary of the 30-day content calendar across channels with weekly themes."
        ),
        content_calendar_table_markdown=(
            "| Day | Theme | Description |\n"
            "| 1 | Brand story | Post about dealership heritage |\n"
            "| 2 | Test drives | Invite for weekend test drives |"
        ),
        kpi_framework="KPIs focused on inquiries, test drives, and showroom visits.",
        measurement_plan="Measure leads from ads, organic, and events; weekly review cadence.",
        next_30_days_action_plan="Concrete tasks for the next 30 days across paid, owned, and earned.",
    )


@pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="WeasyPrint not available in test environment")
def test_render_agency_report_pdf_produces_non_empty_pdf():
    report = _fake_report()
    pdf_bytes = render_agency_report_pdf(report=report, template_name=TEMPLATE_NAME)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0


@pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="WeasyPrint not available in test environment")
def test_render_agency_report_pdf_raises_blank_pdf_for_empty_content():
    # extremely minimal content should fail the text length check
    report = AgencyReport(
        brand_name="Test Brand",
        industry="Automotive",
        primary_goal="Goal",
        target_audience="Audience",
        positioning_summary="Pos",
        executive_summary=".",
        situation_analysis=".",
        key_insights=".",
        strategy=".",
        strategic_pillars=["."],
        messaging_pyramid=".",
        campaign_big_idea=".",
        campaign_concepts=["."],
        content_calendar_summary=".",
        content_calendar_table_markdown=".",
        kpi_framework=".",
        measurement_plan=".",
        next_30_days_action_plan=".",
    )

    with pytest.raises(BlankPdfError):
        render_agency_report_pdf(report=report, template_name=TEMPLATE_NAME)
