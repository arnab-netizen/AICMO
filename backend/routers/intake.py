"""FastAPI Endpoints for Intake Forms & Report Templates."""

from __future__ import annotations

from enum import Enum

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse, StreamingResponse

from backend.schemas import (
    ClientIntakeForm,
    MarketingPlanReport,
    CampaignBlueprintReport,
    SocialCalendarReport,
    PerformanceReviewReport,
)
from backend.templates import (
    generate_client_intake_text_template,
    generate_blank_marketing_plan_template,
    generate_blank_campaign_blueprint_template,
    generate_blank_social_calendar_template,
    generate_blank_performance_review_template,
)
from backend.pdf_utils import text_to_pdf_bytes


class TemplateFormat(str, Enum):
    json = "json"
    text = "text"
    pdf = "pdf"


class ReportType(str, Enum):
    marketing_plan = "marketing_plan"
    campaign_blueprint = "campaign_blueprint"
    social_calendar = "social_calendar"
    performance_review = "performance_review"


router = APIRouter(prefix="/aicmo", tags=["intake-and-reports"])


# =====================
# INPUT – CLIENT FORM
# =====================


@router.get(
    "/templates/intake",
    response_class=PlainTextResponse,
    summary="Get blank client intake form (text/PDF/JSON schema).",
)
def get_blank_intake_template(fmt: TemplateFormat = TemplateFormat.text):
    """
    Retrieve the blank client intake form in the specified format.
    - text: human-readable form for PDF printing or Word editing
    - json: Pydantic schema for programmatic form building
    - pdf: ready-to-print PDF file
    """
    if fmt == TemplateFormat.text:
        return generate_client_intake_text_template()
    elif fmt == TemplateFormat.json:
        # return Pydantic schema so you can build forms programmatically
        return JSONResponse(ClientIntakeForm.model_json_schema())
    elif fmt == TemplateFormat.pdf:
        text = generate_client_intake_text_template()
        pdf_bytes = text_to_pdf_bytes(text)
        return StreamingResponse(
            content=iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="aicmo_intake_form.pdf"'},
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


@router.post(
    "/intake/json",
    summary="Submit a filled client intake form as JSON.",
)
def submit_intake_json(payload: ClientIntakeForm):
    """
    Submit a completed client intake form as JSON.
    In production, this would store in DB and trigger AICMO processing.
    """
    return {
        "status": "ok",
        "message": "Intake received",
        "brand_name": payload.brand.brand_name,
    }


@router.post(
    "/intake/file",
    summary="Submit a filled client intake form as text or PDF file.",
)
async def submit_intake_file(file: UploadFile = File(...)):
    """
    Submit a completed client intake form as a file (text or PDF).

    For now, we accept:
      - text/plain: parse later / manual mapping
      - application/pdf: store for human/AI extraction later

    In production you can plug in OCR or PDF-form parsing.
    """
    content = await file.read()

    if file.content_type == "text/plain":
        # Here you'd implement a parser from the text template → ClientIntakeForm
        # For now we just store/echo meta.
        return {
            "status": "ok",
            "message": "Text intake received",
            "filename": file.filename,
            "size_bytes": len(content),
        }

    if file.content_type == "application/pdf":
        # Same: store in object storage; later run PDF extraction.
        return {
            "status": "ok",
            "message": "PDF intake received",
            "filename": file.filename,
            "size_bytes": len(content),
        }

    raise HTTPException(
        status_code=400, detail="Only text/plain or application/pdf supported for now"
    )


# =====================
# OUTPUT – BLANK REPORT TEMPLATES
# =====================


@router.get(
    "/templates/report/{report_type}",
    summary="Get blank standardized report template for client-side review.",
)
def get_blank_report_template(
    report_type: ReportType,
    fmt: TemplateFormat = TemplateFormat.text,
):
    """
    Retrieve a blank report template in the specified format.

    Report types:
      - marketing_plan: Strategic marketing plan with situation analysis & pillars
      - campaign_blueprint: Single campaign strategy & creative direction
      - social_calendar: Weekly/monthly content calendar
      - performance_review: Monthly KPI review with recommendations

    Formats:
      - text: human-readable form
      - json: Pydantic schema for programmatic building
      - pdf: ready-to-print PDF
    """
    if report_type == ReportType.marketing_plan:
        text = generate_blank_marketing_plan_template()
        schema = MarketingPlanReport.model_json_schema()
        filename = "aicmo_marketing_plan"
    elif report_type == ReportType.campaign_blueprint:
        text = generate_blank_campaign_blueprint_template()
        schema = CampaignBlueprintReport.model_json_schema()
        filename = "aicmo_campaign_blueprint"
    elif report_type == ReportType.social_calendar:
        text = generate_blank_social_calendar_template()
        schema = SocialCalendarReport.model_json_schema()
        filename = "aicmo_social_calendar"
    elif report_type == ReportType.performance_review:
        text = generate_blank_performance_review_template()
        schema = PerformanceReviewReport.model_json_schema()
        filename = "aicmo_performance_review"
    else:
        raise HTTPException(status_code=400, detail="Unsupported report type")

    if fmt == TemplateFormat.text:
        return PlainTextResponse(text)
    elif fmt == TemplateFormat.json:
        return JSONResponse(schema)
    elif fmt == TemplateFormat.pdf:
        pdf_bytes = text_to_pdf_bytes(text)
        return StreamingResponse(
            content=iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


# =====================
# OUTPUT – ACCEPT FILLED REPORTS (OPTIONAL)
# =====================


@router.post("/reports/marketing_plan", summary="Submit a filled marketing plan report.")
def submit_marketing_plan(report: MarketingPlanReport):
    """
    Submit a completed marketing plan report.
    You can store in DB, send to client, or feed back into simulator.
    """
    return {"status": "ok", "type": "marketing_plan", "brand_name": report.brand_name}


@router.post("/reports/campaign_blueprint", summary="Submit a filled campaign blueprint report.")
def submit_campaign_blueprint(report: CampaignBlueprintReport):
    """Submit a completed campaign blueprint report."""
    return {
        "status": "ok",
        "type": "campaign_blueprint",
        "campaign_name": report.campaign_name,
    }


@router.post("/reports/social_calendar", summary="Submit a filled social calendar report.")
def submit_social_calendar(report: SocialCalendarReport):
    """Submit a completed social content calendar."""
    return {"status": "ok", "type": "social_calendar", "brand_name": report.brand_name}


@router.post("/reports/performance_review", summary="Submit a filled performance review report.")
def submit_performance_review(report: PerformanceReviewReport):
    """Submit a completed performance review report."""
    return {"status": "ok", "type": "performance_review", "brand_name": report.brand_name}
