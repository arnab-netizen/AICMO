"""FastAPI main app: Day-1 intake + Day-2 AICMO operator endpoints."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict

from dotenv import load_dotenv

# Load .env automatically when backend starts
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# noqa: E402 - imports after load_dotenv are intentional (FastAPI pattern)
from fastapi import FastAPI, UploadFile, File, HTTPException, Form  # noqa: E402
from fastapi.responses import PlainTextResponse, JSONResponse, StreamingResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

# Phase 5: Learning store + industry presets + LLM enhancement
from backend.learning_usage import record_learning_from_output  # noqa: E402
from backend.llm_enhance import enhance_with_llm as enhance_with_llm_new  # noqa: E402
from backend.generators.marketing_plan import generate_marketing_plan  # noqa: E402
from backend.generators.common_helpers import sanitize_output  # noqa: E402
from backend.agency_grade_enhancers import apply_agency_grade_enhancements  # noqa: E402

from backend.export_utils import (  # noqa: E402
    safe_export_pdf,
    safe_export_pptx,
    safe_export_zip,
    safe_export_agency_pdf,
)
from backend.pdf_renderer import render_pdf_from_context, sections_to_html_list  # noqa: E402
from aicmo.presets.industry_presets import list_available_industries  # noqa: E402
from aicmo.generators import (  # noqa: E402
    generate_swot,
    generate_situation_analysis,
    generate_messaging_pillars,
    generate_social_calendar,
    generate_persona,
)

# Phase L: Vector-based memory learning
from backend.services.learning import learn_from_report  # noqa: E402
from aicmo.memory import engine as memory_engine  # noqa: E402
from aicmo.presets.framework_fusion import structure_learning_context  # noqa: E402
from aicmo.generators.agency_grade_processor import process_report_for_agency_grade  # noqa: E402

from aicmo.io.client_reports import (  # noqa: E402
    ClientInputBrief,
    AICMOOutputReport,
    MarketingPlanView,
    CampaignBlueprintView,
    CampaignObjectiveView,
    AudiencePersonaView,
    SocialCalendarView,
    PerformanceReviewView,
    PerfSummaryView,
    CreativesBlock,
    CreativeRationale,
    ChannelVariant,
    ToneVariant,
    MessagingPyramid,
    SWOTBlock,
    CompetitorSnapshot,
    ActionPlan,
    CTAVariant,
    OfferAngle,
    HookInsight,
    generate_output_report_markdown,
)
from backend.schemas import (  # noqa: E402
    ClientIntakeForm,
    MarketingPlanReport,
    CampaignBlueprintReport,
    SocialCalendarReport,
    PerformanceReviewReport,
)
from backend.templates import (  # noqa: E402
    generate_client_intake_text_template,
    generate_blank_marketing_plan_template,
    generate_blank_campaign_blueprint_template,
    generate_blank_social_calendar_template,
    generate_blank_performance_review_template,
)
from backend.pdf_utils import text_to_pdf_bytes  # noqa: E402
from backend.routers.health import router as health_router  # noqa: E402
from backend.api.routes_learn import router as learn_router  # noqa: E402
from backend.services.wow_reports import (  # noqa: E402
    build_wow_report,
)
from aicmo.presets.package_presets import PACKAGE_PRESETS  # noqa: E402
from aicmo.presets.wow_rules import get_wow_rule  # noqa: E402
from backend.humanizer import (  # noqa: E402
    humanize_report_text,
    HumanizerConfig,
)
from backend.industry_config import get_industry_config  # noqa: E402
from backend.generators.social.video_script_generator import (  # noqa: E402
    generate_video_script_for_day,
)
from backend.generators.action.week1_action_plan import (  # noqa: E402
    generate_week1_action_plan,
)
from backend.generators.reviews.review_responder import (  # noqa: E402
    generate_review_responses,
)
from aicmo.analysis.competitor_finder import (  # noqa: E402
    find_competitors_for_brief,
)

# 🔥 Mapping from package display names to preset keys
# Allows code to convert "Strategy + Campaign Pack (Standard)" → "strategy_campaign_standard"
PACKAGE_NAME_TO_KEY = {
    "Quick Social Pack (Basic)": "quick_social_basic",
    "Strategy + Campaign Pack (Standard)": "strategy_campaign_standard",
    "Full-Funnel Growth Suite (Premium)": "full_funnel_growth_suite",
    "Launch & GTM Pack": "launch_gtm_pack",
    "Brand Turnaround Lab": "brand_turnaround_lab",
    "Retention & CRM Booster": "retention_crm_booster",
    "Performance Audit & Revamp": "performance_audit_revamp",
    # Also support preset keys directly (for direct API calls)
    "quick_social_basic": "quick_social_basic",
    "strategy_campaign_standard": "strategy_campaign_standard",
    "strategy_campaign_basic": "strategy_campaign_basic",
    "full_funnel_growth_suite": "full_funnel_growth_suite",
    "launch_gtm_pack": "launch_gtm_pack",
    "brand_turnaround_lab": "brand_turnaround_lab",
    "retention_crm_booster": "retention_crm_booster",
    "performance_audit_revamp": "performance_audit_revamp",
}

# 🔥 FIX #1: Pack-specific section whitelist enforcement
# Ensures Basic packs only get 10 sections, Standard gets 17, Premium gets 21
# Maps WOW package key → list of allowed section IDs
PACK_SECTION_WHITELIST = {
    # Quick Social Pack (Basic) - 10 sections only
    "quick_social_basic": {
        "overview",
        "audience_segments",
        "messaging_framework",
        "content_buckets",
        "weekly_social_calendar",
        "creative_direction_light",
        "hashtag_strategy",
        "platform_guidelines",
        "kpi_plan_light",
        "final_summary",
    },
    # Strategy + Campaign Pack (Standard) - 16 sections
    "strategy_campaign_standard": {
        "overview",
        "campaign_objective",
        "core_campaign_idea",
        "messaging_framework",
        "channel_plan",
        "audience_segments",
        "persona_cards",
        "creative_direction",
        "influencer_strategy",
        "promotions_and_offers",
        "detailed_30_day_calendar",
        "ad_concepts",
        "kpi_and_budget_plan",
        "execution_roadmap",
        "post_campaign_analysis",
        "final_summary",
    },
    # Full-Funnel Growth Suite (Premium) - 23 sections
    "full_funnel_growth_suite": {
        "overview",
        "market_landscape",
        "competitor_analysis",
        "funnel_breakdown",
        "audience_segments",
        "persona_cards",
        "value_proposition_map",
        "messaging_framework",
        "awareness_strategy",
        "consideration_strategy",
        "conversion_strategy",
        "retention_strategy",
        "landing_page_blueprint",
        "email_automation_flows",
        "remarketing_strategy",
        "ad_concepts_multi_platform",
        "creative_direction",
        "full_30_day_calendar",
        "kpi_and_budget_plan",
        "measurement_framework",
        "execution_roadmap",
        "optimization_opportunities",
        "final_summary",
    },
    # Launch & GTM Pack - 13 sections
    "launch_gtm_pack": {
        "overview",
        "market_landscape",
        "product_positioning",
        "messaging_framework",
        "launch_phases",
        "channel_plan",
        "audience_segments",
        "creative_direction",
        "launch_campaign_ideas",
        "content_calendar_launch",
        "ad_concepts",
        "execution_roadmap",
        "final_summary",
    },
    # Brand Turnaround Lab - 14 sections
    "brand_turnaround_lab": {
        "overview",
        "brand_audit",
        "customer_insights",
        "competitor_analysis",
        "problem_diagnosis",
        "new_positioning",
        "messaging_framework",
        "creative_direction",
        "channel_reset_strategy",
        "reputation_recovery_plan",
        "promotions_and_offers",
        "30_day_recovery_calendar",
        "execution_roadmap",
        "final_summary",
    },
    # Retention & CRM Booster - 14 sections (updated with churn_diagnosis)
    "retention_crm_booster": {
        "overview",
        "customer_segments",
        "persona_cards",
        "customer_journey_map",
        "churn_diagnosis",
        "email_automation_flows",
        "sms_and_whatsapp_flows",
        "loyalty_program_concepts",
        "winback_sequence",
        "post_purchase_experience",
        "ugc_and_community_plan",
        "kpi_plan_retention",
        "execution_roadmap",
        "final_summary",
    },
    # Performance Audit & Revamp - 16 sections (with conversion_audit)
    "performance_audit_revamp": {
        "overview",
        "account_audit",
        "campaign_level_findings",
        "creative_performance_analysis",
        "audience_analysis",
        "funnel_breakdown",
        "competitor_benchmark",
        "problem_diagnosis",
        "revamp_strategy",
        "new_ad_concepts",
        "creative_direction",
        "conversion_audit",
        "remarketing_strategy",
        "kpi_reset_plan",
        "execution_roadmap",
        "final_summary",
    },
}


def _safe_persona_label(label: str | None, primary_goal: str | None = None) -> str:
    """Prevent misrouting of goal text into persona / audience labels.

    - If label is empty or equals the primary goal, return a safe generic label.
    - Otherwise return the trimmed label.
    """
    if not label:
        return "ideal customers"
    lbl = label.strip()
    if not lbl:
        return "ideal customers"
    if primary_goal and primary_goal.strip() and lbl == primary_goal.strip():
        return "ideal customers"
    return lbl


def get_allowed_sections_for_pack(wow_package_key: str) -> set[str]:
    """
    Get the set of allowed section IDs for a given WOW package.
    Returns empty set if package not recognized (fail-safe).
    """
    return PACK_SECTION_WHITELIST.get(wow_package_key, set())


# Configure structured logging
from aicmo.logging import configure_logging, get_logger  # noqa: E402

configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# 🔥 FIX #6: Disable learning from HTTP reports (temporarily, until sanitizer is live)
AICMO_ENABLE_HTTP_LEARNING = os.getenv("AICMO_ENABLE_HTTP_LEARNING", "0") == "1"
logger.info(
    f"🔥 [HTTP LEARNING] Status: {'ENABLED' if AICMO_ENABLE_HTTP_LEARNING else 'DISABLED (default)'}"
)

# Configure structured logging
logger = logging.getLogger("aicmo")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class TemplateFormat(str, Enum):
    json = "json"
    text = "text"
    pdf = "pdf"


class ReportType(str, Enum):
    marketing_plan = "marketing_plan"
    campaign_blueprint = "campaign_blueprint"
    social_calendar = "social_calendar"
    performance_review = "performance_review"


class GenerateRequest(BaseModel):
    brief: ClientInputBrief
    generate_marketing_plan: bool = True
    generate_campaign_blueprint: bool = True
    generate_social_calendar: bool = True
    generate_performance_review: bool = False
    generate_creatives: bool = True
    generate_personas: bool = True  # 🔥 FIX #5: Persona card generation flag
    industry_key: Optional[str] = None  # Phase 5: Optional industry preset key
    package_preset: Optional[str] = None  # TURBO: package name
    include_agency_grade: bool = False  # TURBO: enable agency-grade enhancements
    use_learning: bool = False  # Phase L: enable learning context retrieval and injection
    wow_enabled: bool = True  # WOW: Enable WOW template wrapping
    wow_package_key: Optional[str] = None  # WOW: Package key (e.g., "quick_social_basic")
    stage: str = "draft"  # 🔥 FIX #2: Stage for section selection ("draft", "final")


app = FastAPI(title="AICMO API")
app.include_router(health_router, tags=["health"])
app.include_router(learn_router, tags=["learn"])


# ✨ FIX #3: Pre-load training materials at startup
@app.on_event("startup")
async def startup_preload_training():
    """Load training ZIP structure into memory engine at app startup."""
    try:
        logger.info("🚀 AICMO startup: Pre-loading training materials...")
        memory_engine.preload_training_materials()
        logger.info("✅ Training materials loaded successfully")
    except Exception as e:
        logger.error(f"⚠️  Could not pre-load training materials: {e}")
        # Don't fail startup if training materials aren't available


# =====================
# INPUT – CLIENT FORM
# =====================


@app.get(
    "/templates/intake",
    response_class=PlainTextResponse,
    summary="Get blank client intake form (text/PDF/JSON schema).",
)
def get_blank_intake_template(fmt: TemplateFormat = TemplateFormat.text):
    if fmt == TemplateFormat.text:
        return generate_client_intake_text_template()
    elif fmt == TemplateFormat.json:
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


@app.post(
    "/intake/json",
    summary="Submit a filled client intake form as JSON.",
)
def submit_intake_json(payload: ClientIntakeForm):
    return {
        "status": "ok",
        "message": "Intake received",
        "brand_name": payload.brand.brand_name,
    }


@app.post(
    "/intake/file",
    summary="Submit a filled client intake form as text or PDF file.",
)
async def submit_intake_file(file: UploadFile = File(...)):
    content = await file.read()

    if file.content_type == "text/plain":
        return {
            "status": "ok",
            "message": "Text intake received",
            "filename": file.filename,
            "size_bytes": len(content),
        }

    if file.content_type == "application/pdf":
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


@app.get(
    "/templates/report/{report_type}",
    summary="Get blank standardized report template for client-side review.",
)
def get_blank_report_template(
    report_type: ReportType,
    fmt: TemplateFormat = TemplateFormat.text,
):
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


@app.post("/reports/marketing_plan")
def submit_marketing_plan(report: MarketingPlanReport):
    return {"status": "ok", "type": "marketing_plan", "brand_name": report.brand_name}


@app.post("/reports/campaign_blueprint")
def submit_campaign_blueprint(report: CampaignBlueprintReport):
    return {
        "status": "ok",
        "type": "campaign_blueprint",
        "campaign_name": report.campaign_name,
    }


@app.post("/reports/social_calendar")
def submit_social_calendar(report: SocialCalendarReport):
    return {"status": "ok", "type": "social_calendar", "brand_name": report.brand_name}


@app.post("/reports/performance_review")
def submit_performance_review(report: PerformanceReviewReport):
    return {"status": "ok", "type": "performance_review", "brand_name": report.brand_name}


# ============================================================
# DAY 2 – AICMO operator endpoints used by the Streamlit UI
# ============================================================

# ============================================================
# SECTION GENERATORS REGISTRY (Layer 2: Dynamic Content Generation)
# ============================================================
# Maps section_id -> generator function
# This enables dynamic section generation for any pack size (Basic, Standard, Premium, Enterprise)
# Each section_id can be requested independently and generated as needed
# ============================================================


def _gen_overview(
    req: GenerateRequest,
    mp: MarketingPlanView,
    cb: CampaignBlueprintView,
    **kwargs,
) -> str:
    """Generate 'overview' section."""
    b = req.brief.brand
    g = req.brief.goal
    raw = (
        f"**Brand:** {b.brand_name}\n\n"
        f"**Industry:** {b.industry or 'Not specified'}\n\n"
        f"**Primary Goal:** {g.primary_goal or 'Growth'}\n\n"
        f"**Timeline:** {g.timeline or 'Not specified'}\n\n"
        f"This {req.package_preset or 'marketing'} plan provides a comprehensive strategy "
        "to achieve your business objectives through coordinated marketing activities."
    )
    return sanitize_output(raw, req.brief)


def _gen_campaign_objective(req: GenerateRequest, **kwargs) -> str:
    """Generate 'campaign_objective' section."""
    g = req.brief.goal
    raw = (
        f"**Primary Objective:** {g.primary_goal or 'Brand awareness and growth'}\n\n"
        f"**Secondary Objectives:** {g.secondary_goal or 'Lead generation, customer retention'}\n\n"
        f"**Target Timeline:** {g.timeline or '30-90 days'}\n\n"
        f"**Success Metrics:** Increased brand awareness, lead volume, and customer engagement "
        "across key channels."
    )
    return sanitize_output(raw, req.brief)


def _gen_core_campaign_idea(req: GenerateRequest, **kwargs) -> str:
    """Generate 'core_campaign_idea' section."""
    b = req.brief.brand
    s = req.brief.strategy_extras
    raw = (
        f"Position {b.brand_name} as the default choice in {b.industry or 'its category'} "
        "by combining consistent social presence with proof-driven storytelling.\n\n"
        f"**Key Insight:** {s.success_30_days or 'Customers prefer brands that demonstrate clear, repeatable promises backed by concrete proof.'}\n\n"
        "**Campaign Narrative:** From random marketing acts to a structured, repeatable system "
        "that compounds results over time."
    )
    return sanitize_output(raw, req.brief)


def _gen_messaging_framework(
    req: GenerateRequest,
    mp: MarketingPlanView,
    **kwargs,
) -> str:
    """Generate 'messaging_framework' section."""
    b = req.brief.brand
    g = req.brief.goal
    raw = (
        (
            mp.messaging_pyramid.promise
            if mp.messaging_pyramid
            else f"{b.brand_name} will achieve tangible movement towards {g.primary_goal} "
            "through a clear, repeatable marketing system.\n\n"
        )
        + (
            "**Key Messages:**\n"
            + "\n".join(f"- {msg}" for msg in (mp.messaging_pyramid.key_messages or []))
            + "\n\n"
            if mp.messaging_pyramid
            else ""
        )
        + (
            "**Proof Points:**\n"
            + "\n".join(f"- {pp}" for pp in (mp.messaging_pyramid.proof_points or []))
            + "\n\n"
            if mp.messaging_pyramid
            else ""
        )
        + (
            "**Brand Values:** " + ", ".join(mp.messaging_pyramid.values or []) + "\n"
            if mp.messaging_pyramid
            else ""
        )
    )
    return sanitize_output(raw, req.brief)


def _gen_channel_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'channel_plan' section."""
    raw = (
        "**Primary Channels:** Instagram, LinkedIn, Email\n\n"
        "**Secondary Channels:** X, YouTube, Paid Ads\n\n"
        "**Content Strategy:** Reuse 3–5 core ideas across channels with platform-specific "
        "optimization. Focus on consistency and repetition rather than constant new ideas.\n\n"
        "**Posting Frequency:** 1 post per day per platform, with 2 reels/videos per week."
    )
    return sanitize_output(raw, req.brief)


def _gen_audience_segments(req: GenerateRequest, **kwargs) -> str:
    """Generate 'audience_segments' section."""
    b = req.brief.brand
    a = req.brief.audience
    # Use safe persona label to avoid goal text being echoed as audience
    primary_label = _safe_persona_label(
        a.primary_customer, getattr(req.brief.goal, "primary_goal", None)
    )
    secondary_label = a.secondary_customer or "Referral sources and advocates"

    raw = (
        f"**Primary Audience:** {primary_label}\n"
        f"- {primary_label} actively seeking {b.product_service or 'solutions'}\n"
        f"- Values clarity, proof, and low friction\n\n"
        f"**Secondary Audience:** {secondary_label}\n"
        f"- Decision influencers and advocates\n"
        f"- Shares and amplifies proof-driven content\n\n"
        "**Messaging Approach:** Speak to the specific challenges and aspirations of each segment."
    )
    return sanitize_output(raw, req.brief)


def _gen_persona_cards(
    req: GenerateRequest,
    cb: CampaignBlueprintView,
    **kwargs,
) -> str:
    """Generate 'persona_cards' section."""
    raw = (
        "**Core Buyer Persona: The Decision-Maker**\n\n"
        f"{cb.audience_persona.name or 'Core Buyer'}\n\n"
        f"{cb.audience_persona.description or 'Actively seeking solutions and wants less friction, more clarity, and trustworthy proof before committing.'}\n\n"
        "- Pain Points: Time constraints, choice overload, lack of proof\n"
        "- Desires: Clarity, proven systems, efficiency\n"
        "- Content Preference: Case studies, testimonials, walkthroughs"
    )
    return sanitize_output(raw, req.brief)


def _gen_creative_direction(
    req: GenerateRequest,
    **kwargs,
) -> str:
    """Generate 'creative_direction' section."""
    s = req.brief.strategy_extras
    raw = (
        "**Tone & Personality:** "
        + (
            ", ".join(s.brand_adjectives)
            if s.brand_adjectives
            else "reliable, consistent, growth-focused"
        )
        + "\n\n"
        "**Visual Direction:** Clean, professional, proof-oriented. Use logos, testimonials, "
        "metrics, and results-oriented imagery.\n\n"
        "**Key Design Elements:**\n"
        "- Professional typography with strong visual hierarchy\n"
        "- Client logos and social proof\n"
        "- Metrics and results prominently displayed\n"
        "- Consistent color palette and brand elements"
    )
    return sanitize_output(raw, req.brief)


def _gen_influencer_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'influencer_strategy' section."""
    b = req.brief.brand
    raw = (
        f"**Micro-Influencer Partners:** Thought leaders in {b.industry or 'the industry'} "
        "with 10k–100k engaged followers.\n\n"
        "**Co-creation Opportunities:** Case studies, webinar series, shared content campaigns.\n\n"
        "**Measurement:** Engagement rate (>2%), click-through rate, and lead attribution.\n\n"
        "**Budget Allocation:** 15–20% of media spend for influencer partnerships."
    )
    return sanitize_output(raw, req.brief)


def _gen_promotions_and_offers(req: GenerateRequest, **kwargs) -> str:
    """Generate 'promotions_and_offers' section."""
    b = req.brief.brand
    raw = (
        f"**Primary Offer:** Free consultation or audit to demonstrate the value of "
        f"{b.brand_name}'s approach.\n\n"
        "**Secondary Offers:** Email series, webinar, discount for long-term engagement.\n\n"
        "**Timing:** Launch offers strategically every 2 weeks with countdown timers "
        "and clear CTAs.\n\n"
        "**Risk Reversal:** Money-back guarantee or no-commitment trial period."
    )
    return sanitize_output(raw, req.brief)


def _gen_detailed_30_day_calendar(req: GenerateRequest, **kwargs) -> str:
    """Generate 'detailed_30_day_calendar' section."""
    raw = (
        "**Week 1 (Days 1–7):** Brand story and value positioning\n"
        "- 3–4 hero posts introducing the core promise\n"
        "- 2 educational carousel posts about the category\n\n"
        "**Week 2 (Days 8–14):** Social proof and case studies\n"
        "- 3–4 case study or testimonial posts\n"
        "- 2 before/after or transformation posts\n\n"
        "**Week 3 (Days 15–21):** Channel-specific tactics\n"
        "- Platform-optimized content variations\n"
        "- 2 reel/video posts showcasing results\n\n"
        "**Week 4 (Days 22–30):** Calls to action and lead generation\n"
        "- 3 direct CTA posts\n"
        "- Final offer push with countdown timer"
    )
    return sanitize_output(raw, req.brief)


def _gen_email_and_crm_flows(req: GenerateRequest, **kwargs) -> str:
    """Generate 'email_and_crm_flows' section."""
    raw = (
        "**Welcome Series (3 emails):** Introduce value, share proof, invite to offer\n\n"
        "**Educational Series (5 emails):** Deep-dive into core concepts and solutions\n\n"
        "**Offer Series (3 emails):** Soft pitch → Medium pitch → Hard pitch with "
        "deadline countdown\n\n"
        "**Post-Engagement:** Nurture sequence for non-converters, retargeting after "
        "30 days of activity"
    )
    return sanitize_output(raw, req.brief)


def _gen_ad_concepts(req: GenerateRequest, **kwargs) -> str:
    """Generate 'ad_concepts' section."""
    raw = (
        "**Awareness Ads:** Problem-aware hooks showing the cost of poor marketing strategy\n\n"
        "**Consideration Ads:** Feature case studies, results metrics, and proof of effectiveness\n\n"
        "**Conversion Ads:** Direct CTAs with limited-time offers and urgency elements\n\n"
        "**Remarketing Ads:** Targeted to page visitors and email openers with "
        "special retargeting offers"
    )
    return sanitize_output(raw, req.brief)


def _gen_kpi_and_budget_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'kpi_and_budget_plan' section."""
    g = req.brief.goal
    raw = (
        f"**Primary KPIs:**\n"
        f"- Awareness: Reach ({g.primary_goal and 'target audience size'} per week)\n"
        f"- Engagement: Rate (>2% or 500+ interactions per post)\n"
        f"- Conversion: Leads ({g.primary_goal and 'target weekly leads'})\n\n"
        f"**Budget Allocation:**\n"
        f"- Organic/Owned: 40%\n"
        f"- Paid Social: 35%\n"
        f"- Email/CRM: 15%\n"
        f"- Content/Creatives: 10%\n\n"
        f"**Measurement Cadence:** Weekly reporting, monthly analysis, quarterly optimization"
    )
    return sanitize_output(raw, req.brief)


def _gen_execution_roadmap(req: GenerateRequest, **kwargs) -> str:
    """Generate 'execution_roadmap' section."""
    raw = (
        "**Days 1–7:** Finalize messaging, create content bank, set up tracking\n\n"
        "**Days 8–14:** Launch organic social, email sequences, and first paid campaign\n\n"
        "**Days 15–21:** Optimize based on engagement data, launch second paid variant\n\n"
        "**Days 22–30:** Final push with CTAs, collect lead data, prepare monthly report\n\n"
        "**Month 2+:** Iterate based on performance, double down on winners, "
        "test new channels"
    )
    return sanitize_output(raw, req.brief)


def _gen_post_campaign_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'post_campaign_analysis' section."""
    raw = (
        "**Performance Review:** Compare KPIs against targets, identify winners and losers\n\n"
        "**Content Analysis:** Which content themes, formats, and messages drove engagement?\n\n"
        "**Channel Performance:** ROI by platform, cost per lead, conversion rate\n\n"
        "**Learnings:** Document what worked, what didn't, and why for next campaign\n\n"
        "**Recommendations:** Suggest optimization tactics and new opportunities for growth"
    )
    return sanitize_output(raw, req.brief)


def _gen_final_summary(req: GenerateRequest, **kwargs) -> str:
    """Generate 'final_summary' section."""
    b = req.brief.brand
    raw = (
        f"This comprehensive {req.package_preset or 'marketing'} plan positions "
        f"{b.brand_name} for sustained growth through clear strategy, consistent messaging, "
        "and data-driven optimization.\n\n"
        "Success requires commitment to the core narrative, consistent execution across channels, "
        "and monthly performance reviews to guide adjustments.\n\n"
        "By following this roadmap, you'll replace random marketing acts with a repeatable system "
        "that compounds results over time."
    )
    return sanitize_output(raw, req.brief)


# ============================================================
# ADDITIONAL GENERATORS FOR PREMIUM & ENTERPRISE TIERS
# ============================================================


def _gen_campaign_objective(req: GenerateRequest, **kwargs) -> str:
    """Generate 'campaign_objective' section (duplicate for clarity)."""
    g = req.brief.goal
    return (
        f"**Primary Objective:** {g.primary_goal or 'Brand awareness and growth'}\n\n"
        f"**Secondary Objectives:** {g.secondary_goal or 'Lead generation, customer retention'}\n\n"
        f"**Target Timeline:** {g.timeline or '30-90 days'}\n\n"
        f"**Success Metrics:** Increased brand awareness, lead volume, and customer engagement "
        "across key channels."
    )


def _gen_value_proposition_map(req: GenerateRequest, **kwargs) -> str:
    """Generate 'value_proposition_map' section."""
    b = req.brief.brand
    raw = (
        f"**Primary Value:** Position {b.brand_name} as the default choice through clear, "
        "repeatable messaging and proof-driven storytelling.\n\n"
        "**Emotional Value:** Build trust and confidence through transparent, consistent communication.\n\n"
        "**Functional Value:** Deliver measurable outcomes and results in the stated timeline.\n\n"
        "**Differentiation:** Unique combination of clarity, consistency, and proof (vs. competitors' scattered approach)."
    )
    return sanitize_output(raw, req.brief)


def _gen_creative_territories(req: GenerateRequest, **kwargs) -> str:
    """Generate 'creative_territories' section."""
    raw = (
        "**Territory 1: Authority & Proof**\n"
        "- Showcase case studies, testimonials, metrics, and results\n"
        "- Tone: Confident, evidence-based, professional\n\n"
        "**Territory 2: Simplicity & Clarity**\n"
        "- Highlight the contrast between simple systems vs. chaos\n"
        "- Tone: Accessible, warm, solution-focused\n\n"
        "**Territory 3: Growth & Momentum**\n"
        "- Focus on compounding results and long-term ROI\n"
        "- Tone: Inspiring, forward-looking, ambitious"
    )
    return sanitize_output(raw, req.brief)


def _gen_copy_variants(req: GenerateRequest, **kwargs) -> str:
    """Generate 'copy_variants' section."""
    b = req.brief.brand
    raw = (
        "**Variant A (Rational):**\n"
        f"'{b.brand_name} replaces random marketing with a clear, repeatable system that "
        "compounds results over time.'\n\n"
        "**Variant B (Emotional):**\n"
        "'Stop feeling lost in your marketing. Start seeing progress.'\n\n"
        "**Variant C (Provocative):**\n"
        "' Your competitors are still posting randomly. Here's how to pull ahead.'"
    )
    return sanitize_output(raw, req.brief)


def _gen_funnel_breakdown(req: GenerateRequest, **kwargs) -> str:
    """Generate 'funnel_breakdown' section."""
    return (
        "**Awareness Stage:** Reach ideal buyers through organic and paid social\n"
        "- Goals: Visibility, engagement, social proof\n"
        "- Channels: Instagram, LinkedIn, X, YouTube, Paid Ads\n"
        "- Success metric: Impressions, reach, click-through rate\n\n"
        "**Consideration Stage:** Nurture with deeper education and proof\n"
        "- Goals: Trust, confidence, feature education\n"
        "- Channels: Email, webinars, case studies, product demos\n"
        "- Success metric: Email open rate, webinar attendance, demo requests\n\n"
        "**Conversion Stage:** Drive direct action and purchases\n"
        "- Goals: Sales, leads, commitment\n"
        "- Channels: Landing pages, sales calls, paid offers\n"
        "- Success metric: Conversion rate, cost per lead, deal size"
    )


def _gen_awareness_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'awareness_strategy' section."""
    return (
        "**Goal:** Build top-of-mind awareness and initial interest\n\n"
        "**Tactics:**\n"
        "- Content that shows the problem (chaos in marketing)\n"
        "- Social proof (logos, testimonials, metrics)\n"
        "- Consistent brand presence across channels\n"
        "- Strategic paid amplification of organic content\n\n"
        "**Measurement:** Reach, impressions, engagement rate, CTR\n\n"
        "**Duration:** Ongoing, with monthly optimization cycles"
    )


def _gen_consideration_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'consideration_strategy' section."""
    return (
        "**Goal:** Educate and build confidence through deeper engagement\n\n"
        "**Tactics:**\n"
        "- Email nurture series with strategic insights\n"
        "- Case studies and detailed results\n"
        "- Webinars and educational content\n"
        "- Retargeting ads to engaged audiences\n\n"
        "**Measurement:** Email engagement, time-on-page, video watch rate\n\n"
        "**Duration:** 7-14 days per prospect in this stage"
    )


def _gen_conversion_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'conversion_strategy' section."""
    return (
        "**Goal:** Drive direct action, sales, or lead commitment\n\n"
        "**Tactics:**\n"
        "- Clear CTAs with specific offers\n"
        "- Time-limited promotions and urgency\n"
        "- Direct sales conversations\n"
        "- Landing pages with strong benefit focus\n\n"
        "**Measurement:** Conversion rate, cost per conversion, lead quality\n\n"
        "**Duration:** Concentrated push, typically 5-7 days"
    )


def _gen_retention_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'retention_strategy' section."""
    return (
        "**Goal:** Maximize lifetime value and repeat business\n\n"
        "**Tactics:**\n"
        "- Onboarding sequences for new customers\n"
        "- Regular updates and value-adds\n"
        "- Referral incentives\n"
        "- Win-back campaigns for lapsed customers\n\n"
        "**Measurement:** Repeat purchase rate, LTV, churn rate, NPS\n\n"
        "**Duration:** Ongoing post-purchase"
    )


def _gen_sms_and_whatsapp_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'sms_and_whatsapp_strategy' section."""
    return (
        "**SMS Strategy:**\n"
        "- Welcome message with immediate value\n"
        "- Time-sensitive offers and reminders\n"
        "- Transactional updates\n"
        "- 2-3 messages per week max (avoid fatigue)\n\n"
        "**WhatsApp Strategy:**\n"
        "- More conversational, lower frequency\n"
        "- Customer support and proactive outreach\n"
        "- Group messages for community building\n"
        "- 1-2 messages per week\n\n"
        "**Compliance:** Clear opt-in/opt-out, respect user preferences"
    )


def _gen_remarketing_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'remarketing_strategy' section."""
    return (
        "**Strategy:** Re-engage users who showed interest but didn't convert\n\n"
        "**Audiences:**\n"
        "- Website visitors (no purchase)\n"
        "- Email openers (but no click)\n"
        "- Video watchers (>50% watch time)\n"
        "- Cart abandoners\n\n"
        "**Messages:**\n"
        "- Address common objections\n"
        "- Offer new proof/testimonials\n"
        "- Limited-time incentives\n"
        "- Answer FAQs\n\n"
        "**Frequency:** 2-3 touches per person over 14-21 days"
    )


def _gen_optimization_opportunities(req: GenerateRequest, **kwargs) -> str:
    """Generate 'optimization_opportunities' section."""
    return (
        "**Quick Wins (Implement in Days 1-7):**\n"
        "- Refresh all bio/profile sections with stronger CTAs\n"
        "- A/B test 2-3 email subject lines\n"
        "- Create 3 variations of top-performing post\n\n"
        "**Medium-term (Implement in Weeks 2-4):**\n"
        "- Scale paid spend to 2-3 top-performing creatives\n"
        "- Create new email sequences based on engagement data\n"
        "- Develop webinar or case study content\n\n"
        "**Long-term (Implement in Months 2+):**\n"
        "- Build community or loyalty program\n"
        "- Develop partnership/influencer collaborations\n"
        "- Expand to new channels showing promise"
    )


def _gen_industry_landscape(req: GenerateRequest, **kwargs) -> str:
    """Generate 'industry_landscape' section."""
    b = req.brief.brand
    return (
        f"**Category:** {b.industry or 'Your industry'}\n\n"
        "**Market Size & Growth:** [Industry-specific metrics]\n\n"
        "**Key Trends:**\n"
        "- Shift towards remote-first, digital-native solutions\n"
        "- Increased emphasis on proof and transparency\n"
        "- Consolidation of best practices across channels\n\n"
        "**Technology Shifts:** Automation, personalization, data-driven decision making"
    )


def _gen_market_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'market_analysis' section."""
    return (
        "**Target Market Size:** [Define TAM, SAM, SOM]\n\n"
        "**Customer Growth Rate:** [Industry-specific growth data]\n\n"
        "**Economic Factors:**\n"
        "- Budget availability for marketing solutions\n"
        "- Confidence in spending for growth initiatives\n"
        "- ROI expectations and benchmarks\n\n"
        "**Barriers to Entry:** [Competitive landscape, switching costs, etc.]"
    )


def _gen_competitor_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'competitor_analysis' section."""
    return (
        "**Primary Competitors:** [List 3-5 key competitors]\n\n"
        "**Competitive Strengths:** [What they do well]\n\n"
        "**Competitive Weaknesses:** [Gaps and opportunities]\n\n"
        "**Market Positioning:** [How you're different]\n\n"
        "**Pricing & Positioning:** [Competitive positioning matrix]"
    )


def _gen_customer_insights(req: GenerateRequest, **kwargs) -> str:
    """Generate 'customer_insights' section."""
    return (
        "**Primary Pain Points:**\n"
        "- Unclear marketing strategy and fragmented tactics\n"
        "- Inability to measure ROI effectively\n"
        "- Resource constraints (time, budget, expertise)\n\n"
        "**Desired Outcomes:**\n"
        "- Clear, repeatable marketing system\n"
        "- Measurable, consistent results\n"
        "- Reduced time spent on execution\n\n"
        "**Decision Criteria:**\n"
        "- Proof of results (case studies, testimonials)\n"
        "- Clarity of process\n"
        "- Alignment with business goals"
    )


def _gen_customer_journey_map(req: GenerateRequest, **kwargs) -> str:
    """Generate 'customer_journey_map' section."""
    return (
        "**Stage 1: Awareness (Problem Recognition)**\n"
        "- Trigger: Frustration with marketing results or lack of strategy\n"
        "- Touchpoints: Social content, search, word-of-mouth\n"
        "- Goal: Get on their radar\n\n"
        "**Stage 2: Consideration (Evaluation)**\n"
        "- Activities: Website visit, email sign-up, case study download\n"
        "- Concerns: Will this work for us? Can we afford it?\n"
        "- Goal: Build confidence and relevance\n\n"
        "**Stage 3: Decision (Commitment)**\n"
        "- Activities: Demo, proposal, negotiation\n"
        "- Concerns: Implementation, support, ROI timeline\n"
        "- Goal: Close the sale\n\n"
        "**Stage 4: Retention (Loyalty)**\n"
        "- Activities: Onboarding, support, results communication\n"
        "- Goal: Maximize satisfaction and referrals"
    )


def _gen_brand_positioning(req: GenerateRequest, **kwargs) -> str:
    """Generate 'brand_positioning' section."""
    b = req.brief.brand
    return (
        f"**Brand Position:** {b.brand_name} is the strategic partner for brands that want "
        "to replace chaos with clarity.\n\n"
        "**Target Audience:** Mid-market and growth-stage brands seeking predictable, "
        "repeatable marketing systems.\n\n"
        "**Key Differentiators:**\n"
        "- Deep strategic thinking (not just tactics)\n"
        "- Emphasis on proof and transparency\n"
        "- Integrated, multi-channel approach\n"
        "- Clear measurement and optimization\n\n"
        "**Brand Promise:** Consistent, measurable growth through clear strategy and repeatable execution."
    )


def _gen_measurement_framework(req: GenerateRequest, **kwargs) -> str:
    """Generate 'measurement_framework' section."""
    return (
        "**Tier 1 Metrics (Strategic):**\n"
        "- Business impact (revenue, LTV, market share)\n"
        "- Brand health (awareness, preference, NPS)\n\n"
        "**Tier 2 Metrics (Campaign):**\n"
        "- Conversion rate, cost per acquisition, ROAS\n"
        "- Channel performance and contribution\n\n"
        "**Tier 3 Metrics (Tactical):**\n"
        "- Engagement rate, click-through rate, email open rate\n"
        "- Content performance by type and topic\n\n"
        "**Reporting Cadence:**\n"
        "- Weekly: Tactical metrics and quick wins\n"
        "- Monthly: Campaign performance and optimization\n"
        "- Quarterly: Strategic impact and ROI"
    )


def _gen_risk_assessment(req: GenerateRequest, **kwargs) -> str:
    """Generate 'risk_assessment' section."""
    return (
        "**Market Risk:** Competitive pressure, market saturation\n"
        "- Mitigation: Clear differentiation, continuous innovation\n\n"
        "**Execution Risk:** Team capability, resource constraints\n"
        "- Mitigation: Clear processes, training, dedicated support\n\n"
        "**Messaging Risk:** Market may not resonate with positioning\n"
        "- Mitigation: A/B testing, customer feedback loops, rapid iteration\n\n"
        "**Economic Risk:** Budget cuts, reduced marketing spend\n"
        "- Mitigation: Demonstrate ROI, focus on efficient channels, build long-term contracts"
    )


def _gen_strategic_recommendations(req: GenerateRequest, **kwargs) -> str:
    """Generate 'strategic_recommendations' section."""
    return (
        "**Immediate Actions (Next 30 Days):**\n"
        "1. Launch integrated campaign with core messaging\n"
        "2. Build customer testimonial and case study bank\n"
        "3. Establish weekly reporting dashboard\n\n"
        "**6-Month Objectives:**\n"
        "1. Achieve market leadership in category awareness\n"
        "2. Build referral engine (30%+ of new business)\n"
        "3. Establish thought leadership through content\n\n"
        "**12-Month Vision:**\n"
        "1. Become default choice in category\n"
        "2. Build predictable, scalable marketing system\n"
        "3. Achieve 3x ROI on marketing investment"
    )


def _gen_cxo_summary(req: GenerateRequest, **kwargs) -> str:
    """Generate 'cxo_summary' section (C-suite/executive summary)."""
    b = req.brief.brand
    g = req.brief.goal
    return (
        "**Executive Overview**\n\n"
        f"This strategic campaign plan positions {b.brand_name} to achieve {g.primary_goal or 'significant growth'} "
        "through integrated, data-driven marketing execution.\n\n"
        "**Business Impact:**\n"
        "- Expected revenue impact: [TBD based on campaign performance]\n"
        "- Timeline to profitability: 90+ days\n"
        "- Risk level: Low (proven methodology, clear execution)\n\n"
        "**Investment Required:** [Budget allocation for full execution]\n\n"
        "**Success Indicators:**\n"
        "- Week 1-2: Campaign launch and initial engagement\n"
        "- Week 3-4: Lead generation and conversion signals\n"
        "- Month 2-3: Revenue impact and ROI visibility\n\n"
        "**Recommendation:** Proceed with full implementation with dedicated resources and monthly optimization reviews."
    )


def _gen_landing_page_blueprint(req: GenerateRequest, **kwargs) -> str:
    """Generate 'landing_page_blueprint' section for Premium pack."""
    b = req.brief.brand
    return (
        f"**Landing Page Purpose:** Drive conversions for {req.brief.goal.primary_goal or 'primary offer'}\n\n"
        "**Page Structure:**\n"
        "1. **Hero Section** - Compelling headline, subheading, CTA\n"
        f"   - Headline: [Lead with primary benefit for {b.target_audience or 'target audience'}]\n"
        "   - Hero image: [Product/benefit visualization]\n\n"
        "2. **Value Proposition** - 3-5 key benefits with icons\n"
        "   - Benefit 1: [Key differentiator]\n"
        "   - Benefit 2: [Competitive advantage]\n"
        "   - Benefit 3: [Customer success proof]\n\n"
        "3. **Social Proof** - Testimonials, case studies, statistics\n"
        "   - 2-3 customer testimonials with photos\n"
        "   - Case study: [Specific result achieved]\n"
        "   - Stats: [Quantified benefit]\n\n"
        "4. **Feature Deep-Dive** - How it works, key features\n"
        "   - Feature comparison table\n"
        "   - Step-by-step explanation with visuals\n\n"
        "5. **FAQ Section** - Address common objections\n"
        "   - Top 5-7 objection-handling questions\n\n"
        "6. **CTA Section** - Multiple conversion points\n"
        "   - Primary CTA (signup/purchase)\n"
        "   - Secondary CTA (demo/trial)\n"
        "   - Form fields: [Name, Email, Company]\n\n"
        "7. **Trust Signals** - Security badges, certifications, guarantees\n\n"
        "**Success Metrics:** Click-through rate to form, form completion rate, conversion rate"
    )


def _gen_churn_diagnosis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'churn_diagnosis' section for CRM pack."""
    return (
        "**Churn Analysis Framework**\n\n"
        "**1. Churn Rate by Customer Segment**\n"
        "- High-value customers: [X% annual churn]\n"
        "- Mid-tier customers: [Y% annual churn]\n"
        "- Low-engagement: [Z% annual churn]\n\n"
        "**2. Top Churn Drivers (Exit Interview Analysis)**\n"
        "- Better product elsewhere (35%)\n"
        "- Pricing concerns (25%)\n"
        "- Poor support experience (20%)\n"
        "- Unmet feature needs (15%)\n"
        "- Budget cuts/business change (5%)\n\n"
        "**3. Churn Warning Signals (Early Detection)**\n"
        "- Reduced feature usage after Month 3\n"
        "- Decreased support ticket engagement\n"
        "- Payment failures or billing issues\n"
        "- No expansion/upsell adoption\n"
        "- Negative NPS or feedback trends\n\n"
        "**4. Customer Lifecycle Churn Risk**\n"
        "- Onboarding phase (Month 0-2): High risk\n"
        "- Maturity phase (Month 3-12): Medium risk\n"
        "- Expansion phase (Year 2+): Low risk\n\n"
        "**5. Revenue Impact of Churn**\n"
        "- Monthly revenue loss from churn: $[X]\n"
        "- Annual LTV loss: $[Y]\n"
        "- Cost to replace lost customers: [3-5x acquisition cost]\n\n"
        "**Churn Prevention Priority:** Focus on onboarding phase with 30-60 day check-ins"
    )


def _gen_conversion_audit(req: GenerateRequest, **kwargs) -> str:
    """Generate 'conversion_audit' section for Audit pack."""
    return (
        "**Conversion Funnel Analysis**\n\n"
        "**Landing Page Audit:**\n"
        "- Current conversion rate: [X%]\n"
        "- Benchmark rate for industry: [Y%]\n"
        "- Gap analysis: -[Z%] below benchmark\n"
        "- Key issues: [Unclear value prop, weak CTA, poor mobile UX]\n\n"
        "**Checkout Process Audit:**\n"
        "- Cart abandonment rate: [X%]\n"
        "- Checkout completion rate: [Y%]\n"
        "- Average cart value: $[Z]\n"
        "- Issues identified:\n"
        "  - [Surprise fees at final step]\n"
        "  - [Too many form fields (>8)]\n"
        "  - [No guest checkout option]\n"
        "  - [Slow page load (>3 sec)]\n\n"
        "**User Experience Issues:**\n"
        "- Navigation clarity: [Rating]\n"
        "- Form friction points: [Identified]\n"
        "- Mobile experience: [Issues found]\n"
        "- Payment method options: [Limited]\n\n"
        "**Quick Wins (Implement in 1-2 weeks):**\n"
        "1. Remove non-essential form fields\n"
        "2. Add guest checkout option\n"
        "3. Highlight trust signals (SSL, security, guarantees)\n"
        "4. Optimize CTA button (size, color, copy)\n"
        "5. Show progress through checkout steps\n\n"
        "**Expected Impact:** 15-25% improvement in conversion rate"
    )


# ============================================================
# VIDEO SCRIPT & WEEK 1 ACTION PLAN GENERATORS
# ============================================================


def _gen_video_scripts(
    req: GenerateRequest,
    mp: MarketingPlanView,
    **kwargs,
) -> str:
    """Generate 'video_scripts' section with optional video metadata."""
    b = req.brief.brand
    industry = b.industry or "general"
    audience_desc = ", ".join(
        [p.audience_segment or "target audience" for p in (mp.personas or [])]
    )

    # Generate video script metadata for primary social content
    video_metadata = generate_video_script_for_day(
        brand=b.brand_name,
        industry=industry,
        audience=audience_desc or "target audience",
        text_topic=req.brief.goal.primary_goal or "campaign objective",
    )

    # Format as markdown section
    raw = "**Video Script Framework**\n\n"

    if video_metadata.get("video_hook"):
        raw += f"**Hook (0-3 seconds):** {video_metadata['video_hook']}\n\n"

    if video_metadata.get("video_body"):
        raw += "**Body Points:**\n"
        for i, point in enumerate(video_metadata["video_body"], 1):
            raw += f"- Point {i}: {point}\n"
        raw += "\n"

    if video_metadata.get("video_audio_direction"):
        raw += f"**Audio Direction:** {video_metadata['video_audio_direction']}\n\n"

    if video_metadata.get("video_visual_reference"):
        raw += f"**Visual Reference:** {video_metadata['video_visual_reference']}\n\n"

    if not video_metadata:
        raw += "Video script generation framework ready for LLM enhancement pipeline."

    return sanitize_output(raw, req.brief)


def _gen_week1_action_plan(
    req: GenerateRequest,
    **kwargs,
) -> str:
    """Generate 'week1_action_plan' section with 7-day action checklist."""
    report_data = {
        "brand_name": req.brief.brand.brand_name,
        "goals": [req.brief.goal.primary_goal or "growth"],
        "campaign_goals": [req.brief.goal.primary_goal or "growth"],
    }

    week1_output = generate_week1_action_plan(report_data)
    tasks = week1_output.get("week1_plan", [])

    raw = "**Week 1 Action Plan - 7-Day Quick-Start Checklist**\n\n"
    for task in tasks:
        raw += f"- {task}\n"

    raw += (
        "\n**Key Success Factors:**\n"
        "- Execute at least one task each day\n"
        "- Measure engagement and response rates\n"
        "- Document learnings for next week's optimization\n"
        "- Adapt based on real-time performance data"
    )

    return sanitize_output(raw, req.brief)


def _gen_review_responder(
    req: GenerateRequest,
    **kwargs,
) -> str:
    """Generate 'review_responder' section for reputation management."""
    brand = req.brief.brand.brand_name or "your brand"
    raw_reviews = kwargs.get("raw_reviews", "")

    result = generate_review_responses(
        brand=brand,
        negative_reviews_raw=raw_reviews,
    )

    responses = result.get("review_responses", [])
    if not responses:
        return sanitize_output(
            "**Review Response Framework**\n\nNo reviews provided. Paste customer reviews above to generate structured responses.",
            req.brief,
        )

    raw = "**Review Response Framework**\n\n"
    for i, item in enumerate(responses, 1):
        raw += f"**Review {i}:** {item['review']}\n\n"
        raw += "**Response:** [LLM-generated response to address concern and convert to positive sentiment]\n\n"

    return sanitize_output(raw, req.brief)


def _gen_content_buckets(req: GenerateRequest, **kwargs) -> str:
    """Generate 'content_buckets' section for organizing social content themes."""
    raw = (
        "**Bucket 1: Educational Content** (40%)\n"
        "- Industry insights and trends\n"
        "- How-to guides and tips\n"
        "- Best practices and case studies\n\n"
        "**Bucket 2: Inspirational Content** (30%)\n"
        "- Customer success stories\n"
        "- Behind-the-scenes moments\n"
        "- Team spotlights and culture\n\n"
        "**Bucket 3: Promotional Content** (20%)\n"
        "- Product features and updates\n"
        "- Special offers and announcements\n"
        "- Limited-time promotions\n\n"
        "**Bucket 4: Engagement Content** (10%)\n"
        "- Polls and questions\n"
        "- User-generated content\n"
        "- Community interactions"
    )
    return sanitize_output(raw, req.brief)


def _gen_weekly_social_calendar(req: GenerateRequest, **kwargs) -> str:
    """Generate 'weekly_social_calendar' section with posting schedule."""
    raw = (
        "**Monday:**\n"
        "- 9:00 AM: Educational content (LinkedIn/Facebook)\n"
        "- 6:00 PM: Engagement post (all platforms)\n\n"
        "**Wednesday:**\n"
        "- 10:00 AM: Inspirational/behind-the-scenes (Instagram/TikTok)\n"
        "- 5:00 PM: Customer success story (LinkedIn)\n\n"
        "**Friday:**\n"
        "- 9:00 AM: Promotional content (all platforms)\n"
        "- 4:00 PM: Week wrap-up or reflective post\n\n"
        "**Daily:**\n"
        "- Respond to comments and messages within 4 hours\n"
        "- Engage with 5-10 relevant posts from your audience"
    )
    return sanitize_output(raw, req.brief)


def _gen_creative_direction_light(req: GenerateRequest, **kwargs) -> str:
    """Generate 'creative_direction_light' section for basic creative guidelines."""
    b = req.brief.brand
    raw = (
        f"**Brand Voice:** {b.brand_name} communicates with a tone that is [professional/casual/friendly/authoritative]\n\n"
        "**Visual Style:**\n"
        "- Color palette: Brand primary + complementary colors\n"
        "- Fonts: Modern, readable, brand-consistent\n"
        "- Imagery: Real people, authentic moments over stock photos\n\n"
        "**Key Messaging Pillars:**\n"
        "1. Reliability and expertise\n"
        "2. Customer-centric solutions\n"
        "3. Innovation and growth\n\n"
        "**Dos:**\n"
        "- Use consistent brand colors and fonts\n"
        "- Highlight customer benefits\n"
        "- Keep captions concise and engaging\n\n"
        "**Don'ts:**\n"
        "- Use inconsistent branding\n"
        "- Create overly sales-focused content\n"
        "- Post without proofreading"
    )
    return sanitize_output(raw, req.brief)


def _gen_hashtag_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'hashtag_strategy' section with recommended hashtags."""
    b = req.brief.brand
    industry = b.industry or "industry"
    raw = (
        f"**Brand Hashtags:** (Always include)\n"
        f"- #{b.brand_name.replace(' ', '').lower()}\n"
        f"- #[Brand Name]Insider\n"
        f"- #[Brand Name]Community\n\n"
        f"**Industry Hashtags:** (10-15 per post)\n"
        f"- #{industry.replace(' ', '').lower()}\n"
        f"- #[Trend in {industry}]\n"
        f"- #{industry}Insights\n"
        f"- #{industry}Expert\n\n"
        "**Trending Hashtags:** (5-7 per post)\n"
        "- Research weekly trends in your niche\n"
        "- Use tools like Hashtagify or Sprout Social\n"
        "- Rotate based on seasonal relevance\n\n"
        "**Posting Tips:**\n"
        "- Mix 50/50 branded and trending hashtags\n"
        "- Place hashtags in first comment for cleaner look\n"
        "- Test hashtag combinations for engagement"
    )
    return sanitize_output(raw, req.brief)


def _gen_platform_guidelines(req: GenerateRequest, **kwargs) -> str:
    """Generate 'platform_guidelines' section with platform-specific strategies."""
    raw = (
        "**LinkedIn:**\n"
        "- Focus: B2B insights, thought leadership, industry trends\n"
        "- Format: Long-form articles, professional updates\n"
        "- Posting: 1-2 times per week\n\n"
        "**Facebook:**\n"
        "- Focus: Community building, promotions, customer stories\n"
        "- Format: Mix of text, images, and video\n"
        "- Posting: 3-5 times per week\n\n"
        "**Instagram:**\n"
        "- Focus: Visual storytelling, behind-the-scenes, aesthetics\n"
        "- Format: High-quality images, Reels, Stories\n"
        "- Posting: 4-5 times per week\n\n"
        "**TikTok/Twitter:**\n"
        "- Focus: Trends, quick tips, real-time engagement\n"
        "- Format: Short, authentic, timely content\n"
        "- Posting: 3-5 times per week\n\n"
        "**General Rules:**\n"
        "- Respond to all comments within 24 hours\n"
        "- Use platform-native features (Stories, Reels, Polls)\n"
        "- Monitor platform analytics weekly"
    )
    return sanitize_output(raw, req.brief)


def _gen_kpi_plan_light(req: GenerateRequest, **kwargs) -> str:
    """Generate 'kpi_plan_light' section with simplified KPI framework."""
    raw = (
        "**Monthly KPI Targets:**\n\n"
        "**Reach & Awareness:**\n"
        "- Total impressions: 10,000+\n"
        "- New followers: 100+\n"
        "- Post reach: Avg 500+ per post\n\n"
        "**Engagement:**\n"
        "- Engagement rate: 2-5%\n"
        "- Average comments: 5-10 per post\n"
        "- Shares: 2-5 per post\n\n"
        "**Conversion:**\n"
        "- Link clicks: 20-50 per month\n"
        "- Website traffic from social: 100+ sessions\n"
        "- Lead sign-ups: 5-10 per month\n\n"
        "**Measurement Cadence:**\n"
        "- Weekly: Monitor engagement and top performers\n"
        "- Monthly: Review full-month analytics and adjust strategy\n"
        "- Quarterly: Conduct deep-dive analysis and plan next quarter\n\n"
        "**Success Benchmark:**\n"
        "- Month 1: Establish baseline\n"
        "- Month 2-3: 20-30% improvement\n"
        "- Month 4+: Sustained growth and optimization"
    )
    return sanitize_output(raw, req.brief)


def _gen_30_day_recovery_calendar(req: GenerateRequest, **kwargs) -> str:
    """Generate '30_day_recovery_calendar' section - strategy recovery over 30 days."""
    raw = (
        "**Week 1: Foundation & Quick Wins**\n"
        "- Audit current state (budget, performance, messaging)\n"
        "- Implement 3 quick-win optimizations\n"
        "- Establish daily monitoring dashboard\n"
        "- Restart stakeholder communication\n\n"
        "**Week 2: Strategic Reset**\n"
        "- Refine messaging and creative direction\n"
        "- Launch refreshed campaigns on top-performing channels\n"
        "- Test new audience segments\n"
        "- Prepare case study content\n\n"
        "**Week 3: Momentum & Scaling**\n"
        "- Scale successful experiments from Week 2\n"
        "- Implement advanced targeting refinements\n"
        "- Launch secondary campaigns\n"
        "- Report first positive results\n\n"
        "**Week 4: Optimization & Planning**\n"
        "- Consolidate learnings into repeatable system\n"
        "- Plan next phase (90-day roadmap)\n"
        "- Establish new KPI targets\n"
        "- Schedule monthly reviews"
    )
    return sanitize_output(raw, req.brief)


def _gen_account_audit(req: GenerateRequest, **kwargs) -> str:
    """Generate 'account_audit' section - audit of existing account performance."""
    raw = (
        "**Account Health Assessment**\n"
        "- Overall account status: [Stagnant/Declining/Growing]\n"
        "- Historical spend and ROI trends\n"
        "- Current conversion funnel gaps\n\n"
        "**Performance by Channel**\n"
        "- Organic social performance\n"
        "- Paid social efficiency (CPC, CPL, ROAS)\n"
        "- Email and CRM engagement\n"
        "- Website conversion metrics\n\n"
        "**Key Issues Identified**\n"
        "- Budget waste areas\n"
        "- Underperforming audience segments\n"
        "- Messaging misalignment\n"
        "- Operational bottlenecks\n\n"
        "**Immediate Actions Recommended**\n"
        "1. Pause low-performing campaigns\n"
        "2. Reallocate budget to high-ROI channels\n"
        "3. Update creative and messaging\n"
        "4. Implement daily monitoring"
    )
    return sanitize_output(raw, req.brief)


def _gen_ad_concepts_multi_platform(req: GenerateRequest, **kwargs) -> str:
    """Generate 'ad_concepts_multi_platform' - multi-platform ad concepts."""
    raw = (
        "**LinkedIn Ads**\n"
        "- Headline: Thought leadership and ROI-focused\n"
        "- Format: Lead generation forms, content downloads\n"
        "- CTA: 'Download Guide', 'Schedule Demo'\n\n"
        "**Facebook/Instagram Ads**\n"
        "- Visuals: User-generated content, customer testimonials\n"
        "- Copy: Benefit-focused with urgency\n"
        "- Format: Carousel ads, video ads\n"
        "- CTA: 'Learn More', 'Shop Now'\n\n"
        "**Google Search Ads**\n"
        "- Headlines: Keyword + benefit pairing\n"
        "- Copy: Problem-solution-proof structure\n"
        "- CTA: 'Get Started', 'Claim Offer'\n\n"
        "**TikTok/YouTube Ads**\n"
        "- Format: Short-form video (15-30 seconds)\n"
        "- Tone: Authentic, behind-the-scenes\n"
        "- CTA: On-screen or voice-over call-to-action"
    )
    return sanitize_output(raw, req.brief)


def _gen_audience_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'audience_analysis' section."""
    raw = (
        "**Primary Audience Segment**\n"
        "- Demographics: Age, income, location, education\n"
        "- Psychographics: Values, interests, pain points\n"
        "- Behaviors: Purchase frequency, brand loyalty, channel preference\n"
        "- Size & ROI potential\n\n"
        "**Secondary & Tertiary Segments**\n"
        "- Growth opportunity audiences\n"
        "- Retention-focused segments\n"
        "- High-LTV but hard-to-reach audiences\n\n"
        "**Audience Gaps & Blind Spots**\n"
        "- Underserved micro-segments\n"
        "- Competitor audience targets\n"
        "- Expansion opportunity markets\n\n"
        "**Channel Preferences by Segment**\n"
        "- Where each segment spends time\n"
        "- Preferred content formats\n"
        "- Best times to reach them"
    )
    return sanitize_output(raw, req.brief)


def _gen_brand_audit(req: GenerateRequest, **kwargs) -> str:
    """Generate 'brand_audit' section."""
    b = req.brief.brand
    raw = (
        f"**Brand Identity Assessment**\n"
        f"- Brand name: {b.brand_name or 'TBD'}\n"
        f"- Industry: {b.industry or 'TBD'}\n"
        f"- Positioning: [Current perception vs. desired perception]\n"
        f"- Key differentiators\n\n"
        "**Visual & Messaging Audit**\n"
        "- Logo and brand color consistency\n"
        "- Tone of voice alignment\n"
        "- Message hierarchy and clarity\n"
        "- Competitive differentiation\n\n"
        "**Customer Perception Analysis**\n"
        "- Brand awareness level\n"
        "- Sentiment analysis (social listening)\n"
        "- NPS and customer satisfaction trends\n"
        "- Reputation vs. competitors\n\n"
        "**Recommended Brand Improvements**\n"
        "1. Strengthen unique value proposition\n"
        "2. Improve visual consistency\n"
        "3. Align messaging across channels\n"
        "4. Build brand advocacy program"
    )
    return sanitize_output(raw, req.brief)


def _gen_campaign_level_findings(req: GenerateRequest, **kwargs) -> str:
    """Generate 'campaign_level_findings' - findings at campaign level."""
    raw = (
        "**Campaign Performance Summary**\n"
        "- Total reach: X impressions\n"
        "- Engagement rate: X%\n"
        "- Conversion rate: X%\n"
        "- ROI: X% / ROAS: X.Xx\n\n"
        "**Top Performers**\n"
        "- Best-performing ad: [specific headline/creative]\n"
        "- Best-performing audience: [segment name]\n"
        "- Best-performing channel: [platform]\n"
        "- Best-performing time period: [when]\n\n"
        "**Areas of Underperformance**\n"
        "- Lowest-converting audiences\n"
        "- Highest cost-per-result channels\n"
        "- Lowest engagement creative types\n\n"
        "**Key Insights & Recommendations**\n"
        "- What's working and why\n"
        "- What needs improvement\n"
        "- Optimization opportunities\n"
        "- Next phase priorities"
    )
    return sanitize_output(raw, req.brief)


def _gen_channel_reset_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'channel_reset_strategy' - strategy to reset underperforming channels."""
    raw = (
        "**Channel-by-Channel Reset Plan**\n\n"
        "**Organic Social (LinkedIn/Facebook/Instagram)**\n"
        "- Clear old content calendar\n"
        "- Reset posting frequency to 3-5x per week\n"
        "- Launch new content buckets\n"
        "- Rebuild engagement through community activity\n\n"
        "**Paid Social**\n"
        "- Pause all underperforming campaigns\n"
        "- Archive low-converting audiences\n"
        "- Test new audience segments\n"
        "- Implement aggressive A/B testing\n\n"
        "**Email Marketing**\n"
        "- Clean mailing list (remove inactive subscribers)\n"
        "- Reset send frequency based on engagement\n"
        "- Implement segmentation strategy\n"
        "- A/B test subject lines and CTAs\n\n"
        "**Website**\n"
        "- Update homepage messaging\n"
        "- Refresh value proposition\n"
        "- Optimize key conversion pages\n"
        "- Improve site speed and mobile experience"
    )
    return sanitize_output(raw, req.brief)


def _gen_competitor_benchmark(req: GenerateRequest, **kwargs) -> str:
    """Generate 'competitor_benchmark' section - benchmark against competitors."""
    raw = (
        "**Competitor Benchmarking Analysis**\n\n"
        "**Competitor 1 Analysis**\n"
        "- Positioning and messaging\n"
        "- Primary channels and tactics\n"
        "- Content themes and frequency\n"
        "- Estimated budget and performance\n\n"
        "**Competitor 2 Analysis**\n"
        "- Similar metrics and comparison\n\n"
        "**Key Competitive Insights**\n"
        "- Gaps your brand can exploit\n"
        "- Strengths to match or exceed\n"
        "- Messaging angles to differentiate\n"
        "- Audience segments competitors are missing\n\n"
        "**Recommended Competitive Positioning**\n"
        "- Where to compete aggressively\n"
        "- Where to differentiate\n"
        "- Where to avoid direct competition\n"
        "- Your unique angle in the market"
    )
    return sanitize_output(raw, req.brief)


def _gen_content_calendar_launch(req: GenerateRequest, **kwargs) -> str:
    """Generate 'content_calendar_launch' - launch-specific content calendar."""
    raw = (
        "**Pre-Launch (2 weeks before)**\n"
        "- Teasers on social (1-2 per day)\n"
        "- Email to existing audience\n"
        "- Partner outreach\n"
        "- Influencer prep and briefing\n\n"
        "**Launch Week**\n"
        "- Daily social posts with different angles\n"
        "- Blog post/article publish\n"
        "- Press release distribution\n"
        "- Paid amplification surge\n"
        "- Email launch notification\n"
        "- Influencer + partner co-promotion\n\n"
        "**Post-Launch (2 weeks after)**\n"
        "- Customer testimonials and case studies\n"
        "- Behind-the-scenes content\n"
        "- User-generated content amplification\n"
        "- Follow-up email nurture sequences\n\n"
        "**Content Themes**\n"
        "- What problem does this solve?\n"
        "- Who benefits most?\n"
        "- How is it better than alternatives?\n"
        "- Social proof and success stories"
    )
    return sanitize_output(raw, req.brief)


def _gen_creative_performance_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'creative_performance_analysis' section."""
    raw = (
        "**Creative Elements Performance**\n\n"
        "**Headline Performance**\n"
        "- Top-performing headlines: [+40% CTR vs. average]\n"
        "- Bottom-performing headlines: [-30% CTR vs. average]\n"
        "- Patterns: [Curiosity, urgency, benefit-driven]\n\n"
        "**Visual/Video Performance**\n"
        "- Best-performing image type: [authentic photos vs. stock]\n"
        "- Video view-through rate: X%\n"
        "- Animation vs. static performance\n\n"
        "**Copy Performance**\n"
        "- Long-form vs. short-form effectiveness\n"
        "- Emotional vs. logical appeal\n"
        "- Question-based vs. statement-based\n\n"
        "**Creative Recommendations**\n"
        "- What to double down on\n"
        "- What to eliminate\n"
        "- New formats to test\n"
        "- Seasonal/topic variations to explore"
    )
    return sanitize_output(raw, req.brief)


def _gen_customer_segments(req: GenerateRequest, **kwargs) -> str:
    """Generate 'customer_segments' section - detailed customer segmentation."""
    raw = (
        "**Segment 1: High-Value Customers**\n"
        "- Profile: [Detailed description]\n"
        "- Size: X% of customer base\n"
        "- LTV: $X\n"
        "- Preferred channels and messages\n\n"
        "**Segment 2: Growth Opportunity**\n"
        "- Profile: [Detailed description]\n"
        "- Size: X% of market\n"
        "- Conversion potential: X%\n"
        "- Barriers to entry: [list]\n\n"
        "**Segment 3: Retention Focus**\n"
        "- Profile: [Existing customers at risk]\n"
        "- Churn risk: [high/medium/low]\n"
        "- Retention tactics: [personalized offers, loyalty program]\n\n"
        "**Segment-Specific Strategies**\n"
        "- Channel mix by segment\n"
        "- Message personalization\n"
        "- Offer and pricing strategy\n"
        "- Success metrics by segment"
    )
    return sanitize_output(raw, req.brief)


def _gen_email_automation_flows(req: GenerateRequest, **kwargs) -> str:
    """Generate 'email_automation_flows' section - automated email workflows."""
    raw = (
        "**Welcome Series (Immediate)**\n"
        "- Email 1: Welcome + brand intro (Day 0)\n"
        "- Email 2: Best practices guide (Day 2)\n"
        "- Email 3: Customer success story (Day 4)\n"
        "- Email 4: Limited-time offer (Day 7)\n\n"
        "**Nurture Sequence (Ongoing)**\n"
        "- Educational content: 40%\n"
        "- Social proof content: 30%\n"
        "- Promotional offers: 20%\n"
        "- Re-engagement triggers: 10%\n\n"
        "**Trigger-Based Flows**\n"
        "- Abandoned cart: Recover within 1-3 hours\n"
        "- Post-purchase: Onboarding and upsell\n"
        "- Inactivity: Winback campaign after 60 days\n"
        "- Birthday/Anniversary: Personalized offer\n\n"
        "**Measurement & Optimization**\n"
        "- Open rate targets: >25%\n"
        "- Click rate targets: >3%\n"
        "- Conversion rate targets: >1%\n"
        "- A/B test subject lines and send times monthly"
    )
    return sanitize_output(raw, req.brief)


def _gen_full_30_day_calendar(req: GenerateRequest, **kwargs) -> str:
    """Generate 'full_30_day_calendar' section - comprehensive 30-day content calendar."""
    raw = (
        "**Week 1: Foundation & Education**\n"
        "- Day 1-2: Brand intro content\n"
        "- Day 3-4: Educational posts\n"
        "- Day 5-7: Community engagement sprint\n\n"
        "**Week 2: Social Proof**\n"
        "- Customer case study or testimonial\n"
        "- Team spotlight content\n"
        "- User-generated content feature\n"
        "- Industry trend commentary\n\n"
        "**Week 3: Momentum Building**\n"
        "- Promotional campaign launch\n"
        "- Flash sale or limited offer\n"
        "- Webinar or event announcement\n"
        "- Q&A or community engagement\n\n"
        "**Week 4: Consolidation**\n"
        "- Month recap and results\n"
        "- Early bird offer for next month\n"
        "- Testimonial or success metric share\n"
        "- Call-to-action for next step\n\n"
        "**Posting Schedule:**\n"
        "- Monday-Wednesday: 2 posts/day\n"
        "- Thursday-Friday: 1 post/day\n"
        "- Weekends: 1 Sunday wrap-up post"
    )
    return sanitize_output(raw, req.brief)


def _gen_kpi_plan_retention(req: GenerateRequest, **kwargs) -> str:
    """Generate 'kpi_plan_retention' - KPIs focused on retention."""
    raw = (
        "**Retention Metrics**\n\n"
        "**Customer Retention Rate**\n"
        "- Target: >85% year-over-year\n"
        "- Tracked by cohort\n"
        "- Measured monthly and quarterly\n\n"
        "**Churn Rate**\n"
        "- Target: <5% per quarter\n"
        "- Identify churn reasons\n"
        "- Early warning signals\n\n"
        "**Customer Lifetime Value (LTV)**\n"
        "- Target: $X per customer\n"
        "- Increase by: X% YoY\n"
        "- Varies by segment\n\n"
        "**Engagement Metrics**\n"
        "- Email open rates: >25%\n"
        "- Email click rates: >3%\n"
        "- Product/feature adoption: >60%\n"
        "- Net Promoter Score (NPS): >50\n\n"
        "**Reporting Cadence**\n"
        "- Daily: Login rates, feature usage\n"
        "- Weekly: Engagement metrics summary\n"
        "- Monthly: Cohort retention, LTV, NPS\n"
        "- Quarterly: Strategic retention planning"
    )
    return sanitize_output(raw, req.brief)


def _gen_kpi_reset_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'kpi_reset_plan' section - reset KPI targets."""
    raw = (
        "**Baseline Metrics (Current)**\n"
        "- Awareness: X%\n"
        "- Engagement rate: X%\n"
        "- Conversion rate: X%\n"
        "- ROI: X%\n\n"
        "**Month 1 Targets (Conservative)**\n"
        "- Awareness: X% (+10%)\n"
        "- Engagement: X% (+15%)\n"
        "- Conversion: X% (+20%)\n"
        "- ROI: X% (+25%)\n\n"
        "**Month 2-3 Targets (Aggressive)**\n"
        "- Awareness: X% (+25%)\n"
        "- Engagement: X% (+40%)\n"
        "- Conversion: X% (+50%)\n"
        "- ROI: X% (+100%)\n\n"
        "**Monitoring & Adjustment**\n"
        "- Weekly performance reviews\n"
        "- Bi-weekly strategy adjustments\n"
        "- Monthly target recalibration\n"
        "- Quarterly strategic planning\n\n"
        "**Success Criteria**\n"
        "- Hit 80%+ of targets\n"
        "- Achieve positive ROI within 30 days\n"
        "- Demonstrate trend toward targets by month 1"
    )
    return sanitize_output(raw, req.brief)


def _gen_launch_campaign_ideas(req: GenerateRequest, **kwargs) -> str:
    """Generate 'launch_campaign_ideas' section."""
    raw = (
        "**Campaign Idea 1: Early Access**\n"
        "- Target: Existing customers + VIP list\n"
        "- Offer: 24-hour early access + 20% discount\n"
        "- Format: Exclusive email + SMS\n"
        "- Timeline: 48 hours before public launch\n\n"
        "**Campaign Idea 2: Influencer Takeover**\n"
        "- Partner with 3-5 relevant influencers\n"
        "- Format: Social media posts + Stories\n"
        "- Content: Behind-the-scenes + personal reviews\n"
        "- Timeline: Launch day to +7 days\n\n"
        "**Campaign Idea 3: User-Generated Content**\n"
        "- Hashtag campaign: #[BrandLaunch]\n"
        "- Incentive: Feature + prize for best UGC\n"
        "- Format: Instagram/TikTok\n"
        "- Timeline: Launch week\n\n"
        "**Campaign Idea 4: Limited-Time Bonus**\n"
        "- Offer: Exclusive bonus for first 100 buyers\n"
        "- Format: Email + paid ads + social\n"
        "- Timeline: Launch week\n"
        "- Expected uptick: +30-50% conversions"
    )
    return sanitize_output(raw, req.brief)


def _gen_launch_phases(req: GenerateRequest, **kwargs) -> str:
    """Generate 'launch_phases' section - multi-phase launch strategy."""
    raw = (
        "**Phase 1: Awareness (Weeks 1-2)**\n"
        "- Teaser campaign launch\n"
        "- Partner and influencer outreach\n"
        "- Content distribution\n"
        "- Target: Reach 50K impressions\n\n"
        "**Phase 2: Engagement (Weeks 2-3)**\n"
        "- Paid media amplification\n"
        "- Email nurture series\n"
        "- Product launch event or webinar\n"
        "- Target: 10K clicks, 500 leads\n\n"
        "**Phase 3: Conversion (Week 4)**\n"
        "- Limited-time offer\n"
        "- Final push campaigns\n"
        "- Sales team outreach\n"
        "- Target: 100+ conversions\n\n"
        "**Phase 4: Retention (Week 4+)**\n"
        "- Customer onboarding\n"
        "- Nurture sequences\n"
        "- Success metrics tracking\n"
        "- Target: 85%+ retention post-launch"
    )
    return sanitize_output(raw, req.brief)


def _gen_loyalty_program_concepts(req: GenerateRequest, **kwargs) -> str:
    """Generate 'loyalty_program_concepts' section."""
    raw = (
        "**Loyalty Program Model: Points-Based**\n"
        "- 1 point per $1 spent\n"
        "- Points redeemable at 100 points = $10 credit\n"
        "- Tier system: Bronze (0-1K), Silver (1-5K), Gold (5K+)\n"
        "- Perks: Early access, exclusive offers, free shipping\n\n"
        "**Loyalty Program Model: Tiered Membership**\n"
        "- Entry: Free membership, standard benefits\n"
        "- VIP (annual subscription): Priority support + exclusive products\n"
        "- Platinum: Concierge service + monthly surprise gift\n\n"
        "**Engagement Mechanics**\n"
        "- Referral rewards: $10 for successful referral\n"
        "- Social sharing rewards: Points for tagging, sharing\n"
        "- Birthday/Anniversary: Special gift or discount\n"
        "- Review incentives: Points for product reviews\n\n"
        "**Program Metrics**\n"
        "- Member acquisition: X% of customers\n"
        "- Repeat purchase rate: 60%+ vs. 20% non-members\n"
        "- AOV increase: 30-40% for members\n"
        "- Program ROI: 3:1 (revenue per $ spent on rewards)"
    )
    return sanitize_output(raw, req.brief)


def _gen_market_landscape(req: GenerateRequest, **kwargs) -> str:
    """Generate 'market_landscape' section - overview of market dynamics."""
    b = req.brief.brand
    raw = (
        f"**Market Size & Opportunity**\n"
        f"- Total addressable market: $X billion\n"
        f"- {b.industry or 'Your industry'} segment: $X billion\n"
        f"- Growth rate: X% CAGR\n"
        f"- {b.brand_name or 'Your share'} opportunity: $X million\n\n"
        "**Market Trends & Dynamics**\n"
        "- Consumer behavior shifts\n"
        "- Technology disruptions\n"
        "- Regulatory changes\n"
        "- Competitive landscape shifts\n\n"
        "**Customer Buying Patterns**\n"
        "- Seasonality: Peak months are [Jan-March]\n"
        "- Decision cycle: X-month evaluation period\n"
        "- Channel preferences: Digital-first, mobile-optimized\n"
        "- Price sensitivity: Medium\n\n"
        "**Market Entry & Growth Strategy**\n"
        "- Penetration opportunity: Acquire 1% market share = $X revenue\n"
        "- Geographic expansion: Prioritize [region]\n"
        "- Segment expansion: Target [segment] next\n"
        "- Partnership opportunities: [potential partners]"
    )
    return sanitize_output(raw, req.brief)


def _gen_new_ad_concepts(req: GenerateRequest, **kwargs) -> str:
    """Generate 'new_ad_concepts' - fresh ad creative concepts."""
    raw = (
        "**Concept 1: Problem-Aware Hero**\n"
        "- Headline: 'Tired of [problem]?'\n"
        "- Visual: Person frustrated with status quo\n"
        "- CTA: 'See the Solution'\n"
        "- Best for: Cold audiences\n\n"
        "**Concept 2: Proof-Driven Expert**\n"
        "- Headline: 'Proven to increase [metric] by X%'\n"
        "- Visual: Chart, testimonial, or case study\n"
        "- CTA: 'Get Results'\n"
        "- Best for: Consideration stage\n\n"
        "**Concept 3: Social Proof Wave**\n"
        "- Headline: 'Join X,000+ [audience]'\n"
        "- Visual: Customer logos or testimonials\n"
        "- CTA: 'Join the Movement'\n"
        "- Best for: Building FOMO\n\n"
        "**Concept 4: Value-Stacked**\n"
        "- Headline: '$X in value, just $Y today'\n"
        "- Visual: Product showcase or bundle\n"
        "- CTA: 'Claim Offer'\n"
        "- Best for: High-intent audiences"
    )
    return sanitize_output(raw, req.brief)


def _gen_new_positioning(req: GenerateRequest, **kwargs) -> str:
    """Generate 'new_positioning' section - new brand positioning."""
    b = req.brief.brand
    raw = (
        f"**Previous Positioning**\n"
        f"- [Old positioning statement]\n"
        f"- Limitations: [Why it wasn't working]\n\n"
        f"**New Positioning Statement**\n"
        f"{b.brand_name or 'Brand'} is the [category] for [audience]\n"
        f"that [key benefit] unlike [competitor].\n\n"
        "**Supporting Pillars**\n"
        "1. Quality: [Why best in class]\n"
        "2. Value: [Why worth the price]\n"
        "3. Innovation: [What's unique]\n"
        "4. Reliability: [Why to trust]\n\n"
        "**Proof Points**\n"
        "- Case studies demonstrating key benefits\n"
        "- Industry awards or certifications\n"
        "- Customer testimonials\n"
        "- Data/research supporting claims\n\n"
        "**Go-to-Market for New Positioning**\n"
        "- Update all website copy and messaging\n"
        "- Refresh email templates and sequences\n"
        "- Revise sales deck and collateral\n"
        "- Communicate internally to align team"
    )
    return sanitize_output(raw, req.brief)


def _gen_post_purchase_experience(req: GenerateRequest, **kwargs) -> str:
    """Generate 'post_purchase_experience' section."""
    raw = (
        "**Day 0 - Purchase Complete**\n"
        "- Thank you email with order confirmation\n"
        "- Include tracking information\n"
        "- Set expectations for delivery\n"
        "- Introduce post-purchase resources\n\n"
        "**Day 1-3 - Shipping Phase**\n"
        "- Shipping confirmation\n"
        "- Post on social media (thank you post)\n"
        "- Send onboarding guide or how-to\n"
        "- Check-in: 'Are you excited?'\n\n"
        "**Day 3-7 - Delivery & Activation**\n"
        "- Delivery confirmation\n"
        "- Video tutorial or setup guide\n"
        "- Quick survey: 'What do you think?'\n"
        "- Special bonus or accessory offer\n\n"
        "**Day 7-14 - Engagement Phase**\n"
        "- Check-in call or email\n"
        "- Tips and best practices\n"
        "- Community or support group invitation\n"
        "- Referral program introduction\n\n"
        "**Day 30 - Satisfaction Check**\n"
        "- Satisfaction survey\n"
        "- Testimonial or review request\n"
        "- Loyalty program signup\n"
        "- Next product recommendation"
    )
    return sanitize_output(raw, req.brief)


def _gen_problem_diagnosis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'problem_diagnosis' section - root cause analysis."""
    raw = (
        "**Business Problem Identified**\n"
        "- Symptom: [Declining sales, low engagement, high churn]\n"
        "- Scale: [Quantify the impact]\n"
        "- Timeline: [When did this start?]\n"
        "- Previous attempts to fix: [What's been tried]\n\n"
        "**Root Cause Analysis**\n"
        "- Primary cause: [Market shift, competitive pressure, misalignment]\n"
        "- Contributing factors: [Multiple causes]\n"
        "- Why previous solutions failed: [Analysis]\n\n"
        "**Problem Impact**\n"
        "- Revenue impact: $X at risk\n"
        "- Customer impact: X% customer loss\n"
        "- Brand impact: [Reputation damage, market share loss]\n"
        "- Team impact: [Morale, turnover]\n\n"
        "**Constraints & Opportunities**\n"
        "- Budget available: $X\n"
        "- Timeline: X days/weeks to fix\n"
        "- Team capacity: X people available\n"
        "- Quick wins available: [List 2-3]\n"
        "- Longer-term solutions: [Strategic changes needed]"
    )
    return sanitize_output(raw, req.brief)


def _gen_product_positioning(req: GenerateRequest, **kwargs) -> str:
    """Generate 'product_positioning' section - positioning individual products."""
    raw = (
        "**Product 1: Core/Flagship**\n"
        "- Positioning: [The standard, reliable choice]\n"
        "- Target audience: [Mainstream, volume]\n"
        "- Key benefits: [Quality, value, reliability]\n"
        "- Price point: [Mid-market]\n"
        "- Go-to messaging: 'Works for 90% of use cases'\n\n"
        "**Product 2: Premium/High-End**\n"
        "- Positioning: [The best-in-class option]\n"
        "- Target audience: [High-value, professional]\n"
        "- Key benefits: [Exclusive features, performance]\n"
        "- Price point: [Premium]\n"
        "- Go-to messaging: 'For when only the best will do'\n\n"
        "**Product 3: Budget/Entry**\n"
        "- Positioning: [The smart starting point]\n"
        "- Target audience: [Newcomers, budget-conscious]\n"
        "- Key benefits: [Accessibility, simplicity]\n"
        "- Price point: [Budget]\n"
        "- Go-to messaging: 'Great value to get started'\n\n"
        "**Product Positioning Matrix**\n"
        "- Compare on price, quality, features\n"
        "- Show what's unique about each\n"
        "- Prevent cannibalization\n"
        "- Guide upsell/cross-sell strategy"
    )
    return sanitize_output(raw, req.brief)


def _gen_reputation_recovery_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'reputation_recovery_plan' section."""
    raw = (
        "**Crisis Assessment**\n"
        "- Issue: [Specific problem or incident]\n"
        "- Severity: [Critical, high, medium]\n"
        "- Duration: [How long has it been affecting brand]\n"
        "- Visibility: [Social, media, word-of-mouth impact]\n\n"
        "**Immediate Response (24-48 hours)**\n"
        "- Acknowledge the issue publicly\n"
        "- Apologize if appropriate and specific\n"
        "- Outline immediate action steps\n"
        "- Assign point person for all communication\n\n"
        "**Short-Term Recovery (1-4 weeks)**\n"
        "- Implement fixes to underlying problem\n"
        "- Launch positive content campaign\n"
        "- Reach out to customers/influencers with solutions\n"
        "- Monitor and respond to all feedback\n\n"
        "**Long-Term Reputation Building (ongoing)**\n"
        "- Regular positive impact stories\n"
        "- Community service and leadership\n"
        "- Transparent communication\n"
        "- Proactive reputation management\n\n"
        "**Success Metrics**\n"
        "- Sentiment recovery: Move from negative to neutral/positive\n"
        "- Search results: Push negative results down within 30 days\n"
        "- Customer retention: Retain 85%+ of existing customers\n"
        "- New business impact: Return to growth within 60 days"
    )
    return sanitize_output(raw, req.brief)


def _gen_retention_drivers(req: GenerateRequest, **kwargs) -> str:
    """Generate 'retention_drivers' section - what drives customer retention."""
    raw = (
        "**Product/Service Quality**\n"
        "- Reliability and consistency\n"
        "- Innovation and improvements\n"
        "- Feature roadmap transparency\n"
        "- Support responsiveness\n\n"
        "**Relationship & Community**\n"
        "- Personal connection with team\n"
        "- Community of like-minded users\n"
        "- VIP access and recognition\n"
        "- Exclusive events and opportunities\n\n"
        "**Value & Incentives**\n"
        "- Loyalty rewards program\n"
        "- Exclusive pricing for long-term customers\n"
        "- Early access to new features\n"
        "- Personalized offers\n\n"
        "**Learning & Growth**\n"
        "- Training and certification\n"
        "- Best practices content\n"
        "- Industry insights and trends\n"
        "- Success case studies from similar companies\n\n"
        "**Switching Costs**\n"
        "- Ecosystem lock-in (integrations, data)\n"
        "- Customization and setup investment\n"
        "- Team training and expertise\n"
        "- Process dependencies"
    )
    return sanitize_output(raw, req.brief)


def _gen_revamp_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'revamp_strategy' section - comprehensive revamp strategy."""
    raw = (
        "**Foundation Reset**\n"
        "- Audit current state (what's working/broken)\n"
        "- Clarify brand positioning and messaging\n"
        "- Update visual identity if needed\n"
        "- Realign team on new direction\n\n"
        "**Quick Wins (30 days)**\n"
        "- Pause underperforming campaigns\n"
        "- Implement immediate cost savings\n"
        "- Test new messaging and creatives\n"
        "- Rebuild customer relationships\n\n"
        "**Medium-Term Execution (60-90 days)**\n"
        "- Launch new campaign with updated strategy\n"
        "- Build content pipeline and calendar\n"
        "- Implement automation and processes\n"
        "- Train team on new approach\n\n"
        "**Long-Term Sustainability (90+ days)**\n"
        "- Establish metrics and dashboard\n"
        "- Monthly strategy reviews and adjustments\n"
        "- Continuous testing and optimization\n"
        "- Quarterly strategic planning\n\n"
        "**Success Metrics**\n"
        "- 30-day: Show movement on 3+ key metrics\n"
        "- 60-day: Demonstrate positive ROI\n"
        "- 90-day: Establish new baseline and growth trajectory"
    )
    return sanitize_output(raw, req.brief)


def _gen_risk_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'risk_analysis' section - identify and mitigate risks."""
    raw = (
        "**Market Risks**\n"
        "- Economic downturn impact: High probability, high impact\n"
        "- Competitive new entrant: Medium probability, high impact\n"
        "- Technology disruption: Medium probability, high impact\n"
        "- Mitigation: Diversify channels, build defensibility\n\n"
        "**Operational Risks**\n"
        "- Team retention: Key person dependencies\n"
        "- Budget constraints: Limited resources\n"
        "- Timeline pressure: Aggressive goals\n"
        "- Mitigation: Cross-train, prioritize ruthlessly\n\n"
        "**Campaign Risks**\n"
        "- Messaging misalignment: Damaged brand perception\n"
        "- Creative underperformance: Wasted budget\n"
        "- Audience fatigue: Diminishing returns\n"
        "- Mitigation: A/B test first, rotate creative frequently\n\n"
        "**Financial Risks**\n"
        "- Budget overruns: Over-spending on underperforming channels\n"
        "- Revenue shortfall: Goals not achieved\n"
        "- ROI negative: Campaign loses money\n"
        "- Mitigation: Set spending caps, pivot quickly, monitor daily\n\n"
        "**Risk Mitigation Plan**\n"
        "- Daily monitoring dashboard\n"
        "- Weekly risk review meeting\n"
        "- Emergency contingency fund (10% of budget)\n"
        "- Clear escalation procedures"
    )
    return sanitize_output(raw, req.brief)


def _gen_sms_and_whatsapp_flows(req: GenerateRequest, **kwargs) -> str:
    """Generate 'sms_and_whatsapp_flows' section - SMS and WhatsApp strategies."""
    raw = (
        "**SMS Strategy**\n"
        "- Opt-in incentive: [10% off first purchase]\n"
        "- Sending frequency: [2-3x per week max]\n"
        "- Content mix: 40% promotional, 30% educational, 30% urgent/timely\n"
        "- Best time to send: 9-10 AM and 5-6 PM\n\n"
        "**SMS Use Cases**\n"
        "- Order confirmations and shipping updates\n"
        "- Flash sales and limited-time offers\n"
        "- Appointment reminders\n"
        "- Re-engagement campaigns for inactive users\n"
        "- VIP exclusive access\n\n"
        "**WhatsApp Strategy**\n"
        "- Business account setup and verification\n"
        "- Personalized, conversational messaging\n"
        "- Support and customer service integration\n"
        "- Group broadcast lists for segmented messaging\n\n"
        "**WhatsApp Use Cases**\n"
        "- Order status updates with rich media\n"
        "- Personalized product recommendations\n"
        "- Customer support and Q&A\n"
        "- Exclusive offers and previews\n"
        "- Community building and engagement\n\n"
        "**Compliance & Best Practices**\n"
        "- Clear opt-in and opt-out options\n"
        "- Respect quiet hours (9 PM - 8 AM)\n"
        "- Monitor metrics: delivery, open, response rates\n"
        "- Regular list hygiene and inactive removal"
    )
    return sanitize_output(raw, req.brief)


def _gen_turnaround_milestones(req: GenerateRequest, **kwargs) -> str:
    """Generate 'turnaround_milestones' section - key milestones for turnaround."""
    raw = (
        "**Week 1-2 Milestones**\n"
        "✓ Strategy finalized and communicated\n"
        "✓ Team aligned on plan\n"
        "✓ Quick wins identified and launched\n"
        "✓ Monitoring dashboard live\n\n"
        "**Week 3-4 Milestones**\n"
        "✓ First data showing positive movement\n"
        "✓ New creative launched\n"
        "✓ Audience segments tested\n"
        "✓ Customer communication plan activated\n\n"
        "**Month 2 Milestones**\n"
        "✓ 30% improvement on primary KPI\n"
        "✓ New partnerships or integrations active\n"
        "✓ Content calendar live and on schedule\n"
        "✓ Team trained on new processes\n\n"
        "**Month 3 Milestones**\n"
        "✓ ROI positive (revenue > costs)\n"
        "✓ Secondary goals achieved\n"
        "✓ Processes optimized and repeatable\n"
        "✓ Next phase planning complete\n\n"
        "**Success Definition**\n"
        "- Hit 75%+ of planned milestones\n"
        "- Demonstrate clear upward trend\n"
        "- Achieve positive ROI by month 3\n"
        "- Team confidence and momentum"
    )
    return sanitize_output(raw, req.brief)


def _gen_winback_sequence(req: GenerateRequest, **kwargs) -> str:
    """Generate 'winback_sequence' section - win back inactive customers."""
    raw = (
        "**Segment: Inactive Customers (No purchase in 90+ days)**\n"
        "- Email 1 (Day 1): 'We miss you' personal message\n"
        "- Email 2 (Day 3): Special offer: '20% off to return'\n"
        "- Email 3 (Day 7): What's new: Feature updates and improvements\n"
        "- Email 4 (Day 14): Last chance: Limited-time winback offer\n\n"
        "**Segment: Churned Customers (Cancelled subscription)**\n"
        "- Email 1 (Day 1): 'We're sorry to see you go' + feedback request\n"
        "- Email 2 (Day 7): 'Things have changed' - new features since departure\n"
        "- Email 3 (Day 14): Special re-engagement offer\n"
        "- Email 4 (Day 30): Final attempt or remove from sequence\n\n"
        "**Messaging Approach**\n"
        "- Acknowledge the gap ('It's been X months...')\n"
        "- Offer genuine value, not just discounts\n"
        "- Highlight what's new and improved\n"
        "- Make reactivation easy\n\n"
        "**Measurement**\n"
        "- Email open rate: >15% (low engagement)\n"
        "- Click rate: >2% (indication of interest)\n"
        "- Reactivation rate: Target 5-10%\n"
        "- ROI: Track reactivated customer LTV"
    )
    return sanitize_output(raw, req.brief)


# Register all section generators
SECTION_GENERATORS: dict[str, callable] = {
    "overview": _gen_overview,
    "30_day_recovery_calendar": _gen_30_day_recovery_calendar,
    "account_audit": _gen_account_audit,
    "ad_concepts": _gen_ad_concepts,
    "ad_concepts_multi_platform": _gen_ad_concepts_multi_platform,
    "audience_analysis": _gen_audience_analysis,
    "audience_segments": _gen_audience_segments,
    "awareness_strategy": _gen_awareness_strategy,
    "brand_audit": _gen_brand_audit,
    "brand_positioning": _gen_brand_positioning,
    "campaign_level_findings": _gen_campaign_level_findings,
    "campaign_objective": _gen_campaign_objective,
    "channel_plan": _gen_channel_plan,
    "channel_reset_strategy": _gen_channel_reset_strategy,
    "churn_diagnosis": _gen_churn_diagnosis,
    "competitor_analysis": _gen_competitor_analysis,
    "competitor_benchmark": _gen_competitor_benchmark,
    "consideration_strategy": _gen_consideration_strategy,
    "content_buckets": _gen_content_buckets,
    "content_calendar_launch": _gen_content_calendar_launch,
    "conversion_audit": _gen_conversion_audit,
    "conversion_strategy": _gen_conversion_strategy,
    "copy_variants": _gen_copy_variants,
    "core_campaign_idea": _gen_core_campaign_idea,
    "creative_direction": _gen_creative_direction,
    "creative_direction_light": _gen_creative_direction_light,
    "creative_performance_analysis": _gen_creative_performance_analysis,
    "creative_territories": _gen_creative_territories,
    "customer_insights": _gen_customer_insights,
    "customer_journey_map": _gen_customer_journey_map,
    "customer_segments": _gen_customer_segments,
    "cxo_summary": _gen_cxo_summary,
    "detailed_30_day_calendar": _gen_detailed_30_day_calendar,
    "email_and_crm_flows": _gen_email_and_crm_flows,
    "email_automation_flows": _gen_email_automation_flows,
    "execution_roadmap": _gen_execution_roadmap,
    "final_summary": _gen_final_summary,
    "full_30_day_calendar": _gen_full_30_day_calendar,
    "funnel_breakdown": _gen_funnel_breakdown,
    "hashtag_strategy": _gen_hashtag_strategy,
    "industry_landscape": _gen_industry_landscape,
    "influencer_strategy": _gen_influencer_strategy,
    "kpi_and_budget_plan": _gen_kpi_and_budget_plan,
    "kpi_plan_light": _gen_kpi_plan_light,
    "kpi_plan_retention": _gen_kpi_plan_retention,
    "kpi_reset_plan": _gen_kpi_reset_plan,
    "landing_page_blueprint": _gen_landing_page_blueprint,
    "launch_campaign_ideas": _gen_launch_campaign_ideas,
    "launch_phases": _gen_launch_phases,
    "loyalty_program_concepts": _gen_loyalty_program_concepts,
    "market_analysis": _gen_market_analysis,
    "market_landscape": _gen_market_landscape,
    "measurement_framework": _gen_measurement_framework,
    "messaging_framework": _gen_messaging_framework,
    "new_ad_concepts": _gen_new_ad_concepts,
    "new_positioning": _gen_new_positioning,
    "optimization_opportunities": _gen_optimization_opportunities,
    "persona_cards": _gen_persona_cards,
    "platform_guidelines": _gen_platform_guidelines,
    "post_campaign_analysis": _gen_post_campaign_analysis,
    "post_purchase_experience": _gen_post_purchase_experience,
    "problem_diagnosis": _gen_problem_diagnosis,
    "product_positioning": _gen_product_positioning,
    "promotions_and_offers": _gen_promotions_and_offers,
    "remarketing_strategy": _gen_remarketing_strategy,
    "reputation_recovery_plan": _gen_reputation_recovery_plan,
    "retention_drivers": _gen_retention_drivers,
    "retention_strategy": _gen_retention_strategy,
    "revamp_strategy": _gen_revamp_strategy,
    # NOTE: review_responder is implemented + tested but intentionally not wired to any pack.
    # To enable it, add "review_responder" to the relevant pack in aicmo/presets/package_presets.py
    "review_responder": _gen_review_responder,
    "risk_analysis": _gen_risk_analysis,
    "risk_assessment": _gen_risk_assessment,
    "sms_and_whatsapp_flows": _gen_sms_and_whatsapp_flows,
    "sms_and_whatsapp_strategy": _gen_sms_and_whatsapp_strategy,
    "strategic_recommendations": _gen_strategic_recommendations,
    "turnaround_milestones": _gen_turnaround_milestones,
    "ugc_and_community_plan": _gen_promotions_and_offers,  # Reuse promotions for now
    "value_proposition_map": _gen_value_proposition_map,
    "video_scripts": _gen_video_scripts,
    "week1_action_plan": _gen_week1_action_plan,
    "weekly_social_calendar": _gen_weekly_social_calendar,
    "winback_sequence": _gen_winback_sequence,
}


def generate_sections(
    section_ids: list[str],
    req: GenerateRequest,
    mp: MarketingPlanView,
    cb: CampaignBlueprintView,
    cal: SocialCalendarView,
    pr: Optional[PerformanceReviewView] = None,
    creatives: Optional[CreativesBlock] = None,
    action_plan: Optional[ActionPlan] = None,
) -> dict[str, str]:
    """
    Generate content for a specific list of section IDs.

    This is the core Layer 2 function - it takes a list of requested section_ids
    and returns only those sections' content. Works for any pack size (Basic, Standard, Premium, Enterprise).

    QUALITY ENFORCEMENT: All generated sections are validated against benchmarks.
    Failing sections are regenerated once. If validation still fails after regeneration,
    an HTTPException is raised with details.

    Args:
        section_ids: List of section IDs to generate (e.g., ["overview", "persona_cards"])
        req: GenerateRequest with brief and config
        mp, cb, cal, pr, creatives, action_plan: Output components

    Returns:
        Dict mapping section_id -> content (markdown string)

    Raises:
        HTTPException: If sections fail benchmark validation after regeneration
    """
    from backend.validators.report_enforcer import (
        enforce_benchmarks_with_regen,
        BenchmarkEnforcementError,
    )

    results = {}
    context = {
        "req": req,
        "mp": mp,
        "cb": cb,
        "cal": cal,
        "pr": pr,
        "creatives": creatives,
        "action_plan": action_plan,
    }

    # PASS 1: Generate all sections
    for section_id in section_ids:
        generator_fn = SECTION_GENERATORS.get(section_id)
        if generator_fn:
            try:
                results[section_id] = generator_fn(**context)
            except Exception as e:
                # Log error internally for debugging, but don't leak to client
                logger.error(f"Section generator failed for '{section_id}': {e}", exc_info=True)
                # Return empty string instead of error message
                # Downstream aggregator will skip empty sections
                results[section_id] = ""
        else:
            # Section not yet implemented - skip rather than output placeholder
            continue

    # QUALITY GATE: Enforce benchmarks using the enforcer pattern
    pack_key = req.package_preset or req.wow_package_key
    if pack_key and results:
        # Build sections list for validation
        sections_for_validation = [
            {"id": section_id, "content": content}
            for section_id, content in results.items()
            if content  # Skip empty sections
        ]

        if sections_for_validation:

            def regenerate_failed_sections(failing_ids, failing_issues):
                """Regenerate only the failing sections."""
                logger.warning(
                    f"[BENCHMARK ENFORCEMENT] Regenerating {len(failing_ids)} failing section(s): {failing_ids}"
                )

                regenerated = []
                for section_id in failing_ids:
                    generator_fn = SECTION_GENERATORS.get(section_id)
                    if generator_fn:
                        try:
                            content = generator_fn(**context)
                            regenerated.append({"id": section_id, "content": content})
                            logger.info(f"[REGENERATION] Regenerated section: {section_id}")
                        except Exception as e:
                            logger.error(
                                f"[REGENERATION] Failed to regenerate '{section_id}': {e}",
                                exc_info=True,
                            )
                return regenerated

            try:
                enforcement = enforce_benchmarks_with_regen(
                    pack_key=pack_key,
                    sections=sections_for_validation,
                    regenerate_failed_sections=regenerate_failed_sections,
                    max_attempts=2,
                )

                logger.info(
                    f"[BENCHMARK ENFORCEMENT] Pack: {pack_key}, "
                    f"Status: {enforcement.status}, "
                    f"Sections: {len(enforcement.sections)}"
                )

                # Update results with validated sections
                for section in enforcement.sections:
                    section_id = section.get("id") or section.get("section_id")
                    if section_id:
                        results[section_id] = section.get("content", "")

            except BenchmarkEnforcementError as exc:
                logger.error(f"[BENCHMARK ENFORCEMENT] Failed: {exc}")
                raise HTTPException(
                    status_code=500,
                    detail=str(exc),
                )

    return results


def _generate_section_content(
    section_id: str,
    req: GenerateRequest,
    mp: MarketingPlanView,
    cb: CampaignBlueprintView,
    cal: SocialCalendarView,
    pr: Optional[PerformanceReviewView],
    creatives: Optional[CreativesBlock],
    persona_cards: list,
    action_plan: Optional[ActionPlan],
) -> str:
    """
    Generate content for a specific section ID based on the package preset.

    Maps section IDs from the preset to actual content generated in the output.
    This allows WOW templates to reference all 17 sections for strategy_campaign_standard.

    Args:
        section_id: One of the preset section keys (e.g., "overview", "campaign_objective")
        req: GenerateRequest with brief and config
        mp, cb, cal, pr, creatives: Output components
        persona_cards: List of persona cards
        action_plan: Action plan component

    Returns:
        Markdown string for this section
    """
    b = req.brief.brand
    g = req.brief.goal
    a = req.brief.audience
    s = req.brief.strategy_extras

    # Map section IDs to content generation
    section_map = {
        # Core sections
        "overview": (
            f"**Brand:** {b.brand_name}\n\n"
            f"**Industry:** {b.industry or 'Not specified'}\n\n"
            f"**Primary Goal:** {g.primary_goal or 'Growth'}\n\n"
            f"**Timeline:** {g.timeline or 'Not specified'}\n\n"
            f"This {req.package_preset or 'marketing'} plan provides a comprehensive strategy "
            "to achieve your business objectives through coordinated marketing activities."
        ),
        "campaign_objective": (
            f"**Primary Objective:** {g.primary_goal or 'Brand awareness and growth'}\n\n"
            f"**Secondary Objectives:** {g.secondary_goal or 'Lead generation, customer retention'}\n\n"
            f"**Target Timeline:** {g.timeline or '30-90 days'}\n\n"
            f"**Success Metrics:** Increased brand awareness, lead volume, and customer engagement "
            "across key channels."
        ),
        "core_campaign_idea": (
            f"Position {b.brand_name} as the default choice in {b.industry or 'its category'} "
            "by combining consistent social presence with proof-driven storytelling.\n\n"
            f"**Key Insight:** {s.success_30_days or 'Customers prefer brands that demonstrate clear, repeatable promises backed by concrete proof.'}\n\n"
            "**Campaign Narrative:** From random marketing acts to a structured, repeatable system "
            "that compounds results over time."
        ),
        "messaging_framework": (
            mp.messaging_pyramid.promise
            if mp.messaging_pyramid
            else f"{b.brand_name} will achieve tangible movement towards {g.primary_goal} "
            "through a clear, repeatable marketing system.\n\n"
        )
        + (
            "**Key Messages:**\n"
            + "\n".join(f"- {msg}" for msg in (mp.messaging_pyramid.key_messages or []))
            + "\n\n"
            if mp.messaging_pyramid
            else ""
        )
        + (
            "**Proof Points:**\n"
            + "\n".join(f"- {pp}" for pp in (mp.messaging_pyramid.proof_points or []))
            + "\n\n"
            if mp.messaging_pyramid
            else ""
        )
        + (
            "**Brand Values:** " + ", ".join(mp.messaging_pyramid.values or []) + "\n"
            if mp.messaging_pyramid
            else ""
        ),
        "channel_plan": (
            "**Primary Channels:** Instagram, LinkedIn, Email\n\n"
            "**Secondary Channels:** X, YouTube, Paid Ads\n\n"
            "**Content Strategy:** Reuse 3–5 core ideas across channels with platform-specific "
            "optimization. Focus on consistency and repetition rather than constant new ideas.\n\n"
            "**Posting Frequency:** 1 post per day per platform, with 2 reels/videos per week."
        ),
        "audience_segments": (
            f"**Primary Audience:** {a.primary_customer}\n"
            f"- {a.primary_customer} actively seeking {b.product_service or 'solutions'}\n"
            f"- Values clarity, proof, and low friction\n\n"
            f"**Secondary Audience:** {a.secondary_customer or 'Referral sources and advocates'}\n"
            f"- Decision influencers and advocates\n"
            f"- Shares and amplifies proof-driven content\n\n"
            "**Messaging Approach:** Speak to the specific challenges and aspirations of each segment."
        ),
        "persona_cards": (
            "**Core Buyer Persona: The Decision-Maker**\n\n"
            f"{cb.audience_persona.name or 'Core Buyer'}\n\n"
            f"{cb.audience_persona.description or 'Actively seeking solutions and wants less friction, more clarity, and trustworthy proof before committing.'}\n\n"
            "- Pain Points: Time constraints, choice overload, lack of proof\n"
            "- Desires: Clarity, proven systems, efficiency\n"
            "- Content Preference: Case studies, testimonials, walkthroughs"
        ),
        "creative_direction": (
            "**Tone & Personality:** "
            + (
                ", ".join(s.brand_adjectives)
                if s.brand_adjectives
                else "reliable, consistent, growth-focused"
            )
            + "\n\n"
            "**Visual Direction:** Clean, professional, proof-oriented. Use logos, testimonials, "
            "metrics, and results-oriented imagery.\n\n"
            "**Key Design Elements:**\n"
            "- Professional typography with strong visual hierarchy\n"
            "- Client logos and social proof\n"
            "- Metrics and results prominently displayed\n"
            "- Consistent color palette and brand elements"
        ),
        "influencer_strategy": (
            f"**Micro-Influencer Partners:** Thought leaders in {b.industry or 'the industry'} "
            "with 10k–100k engaged followers.\n\n"
            "**Co-creation Opportunities:** Case studies, webinar series, shared content campaigns.\n\n"
            "**Measurement:** Engagement rate (>2%), click-through rate, and lead attribution.\n\n"
            "**Budget Allocation:** 15–20% of media spend for influencer partnerships."
        ),
        "promotions_and_offers": (
            f"**Primary Offer:** Free consultation or audit to demonstrate the value of "
            f"{b.brand_name}'s approach.\n\n"
            "**Secondary Offers:** Email series, webinar, discount for long-term engagement.\n\n"
            "**Timing:** Launch offers strategically every 2 weeks with countdown timers "
            "and clear CTAs.\n\n"
            "**Risk Reversal:** Money-back guarantee or no-commitment trial period."
        ),
        "detailed_30_day_calendar": (
            "**Week 1 (Days 1–7):** Brand story and value positioning\n"
            "- 3–4 hero posts introducing the core promise\n"
            "- 2 educational carousel posts about the category\n\n"
            "**Week 2 (Days 8–14):** Social proof and case studies\n"
            "- 3–4 case study or testimonial posts\n"
            "- 2 before/after or transformation posts\n\n"
            "**Week 3 (Days 15–21):** Channel-specific tactics\n"
            "- Platform-optimized content variations\n"
            "- 2 reel/video posts showcasing results\n\n"
            "**Week 4 (Days 22–30):** Calls to action and lead generation\n"
            "- 3 direct CTA posts\n"
            "- Final offer push with countdown timer"
        ),
        "email_and_crm_flows": (
            "**Welcome Series (3 emails):** Introduce value, share proof, invite to offer\n\n"
            "**Educational Series (5 emails):** Deep-dive into core concepts and solutions\n\n"
            "**Offer Series (3 emails):** Soft pitch → Medium pitch → Hard pitch with "
            "deadline countdown\n\n"
            "**Post-Engagement:** Nurture sequence for non-converters, retargeting after "
            "30 days of activity"
        ),
        "ad_concepts": (
            "**Awareness Ads:** Problem-aware hooks showing the cost of poor marketing strategy\n\n"
            "**Consideration Ads:** Feature case studies, results metrics, and proof of effectiveness\n\n"
            "**Conversion Ads:** Direct CTAs with limited-time offers and urgency elements\n\n"
            "**Remarketing Ads:** Targeted to page visitors and email openers with "
            "special retargeting offers"
        ),
        "kpi_and_budget_plan": (
            f"**Primary KPIs:**\n"
            f"- Awareness: Reach ({g.primary_goal and 'target audience size'} per week)\n"
            f"- Engagement: Rate (>2% or 500+ interactions per post)\n"
            f"- Conversion: Leads ({g.primary_goal and 'target weekly leads'})\n\n"
            f"**Budget Allocation:**\n"
            f"- Organic/Owned: 40%\n"
            f"- Paid Social: 35%\n"
            f"- Email/CRM: 15%\n"
            f"- Content/Creatives: 10%\n\n"
            f"**Measurement Cadence:** Weekly reporting, monthly analysis, quarterly optimization"
        ),
        "execution_roadmap": (
            "**Days 1–7:** Finalize messaging, create content bank, set up tracking\n\n"
            "**Days 8–14:** Launch organic social, email sequences, and first paid campaign\n\n"
            "**Days 15–21:** Optimize based on engagement data, launch second paid variant\n\n"
            "**Days 22–30:** Final push with CTAs, collect lead data, prepare monthly report\n\n"
            "**Month 2+:** Iterate based on performance, double down on winners, "
            "test new channels"
        ),
        "post_campaign_analysis": (
            "**Performance Review:** Compare KPIs against targets, identify winners and losers\n\n"
            "**Content Analysis:** Which content themes, formats, and messages drove engagement?\n\n"
            "**Channel Performance:** ROI by platform, cost per lead, conversion rate\n\n"
            "**Learnings:** Document what worked, what didn't, and why for next campaign\n\n"
            "**Recommendations:** Suggest optimization tactics and new opportunities for growth"
        ),
        "final_summary": (
            f"This comprehensive {req.package_preset or 'marketing'} plan positions "
            f"{b.brand_name} for sustained growth through clear strategy, consistent messaging, "
            "and data-driven optimization.\n\n"
            "Success requires commitment to the core narrative, consistent execution across channels, "
            "and monthly performance reviews to guide adjustments.\n\n"
            "By following this roadmap, you'll replace random marketing acts with a repeatable system "
            "that compounds results over time."
        ),
    }

    # Return the generated content for this section, or a placeholder if not found
    return section_map.get(section_id, f"[{section_id} content to be populated]")


def _generate_stub_output(req: GenerateRequest) -> AICMOOutputReport:
    """
    Stub generator (internal).
    - Uses brief to build deterministic, client-ready structures.
    - Includes messaging pyramid, SWOT, competitor snapshot,
      persona cards, action plan and creatives with rationale.
    """
    b = req.brief.brand
    g = req.brief.goal
    a = req.brief.audience
    s = req.brief.strategy_extras
    today = date.today()

    # Messaging pyramid, SWOT, competitor snapshot
    messaging_pyramid = MessagingPyramid(
        promise=s.success_30_days
        or f"{b.brand_name} will see tangible movement towards {g.primary_goal or 'key business goals'} in the next 30 days.",
        key_messages=[
            "We replace random acts of marketing with a simple, repeatable system.",
            "We reuse a few strong ideas across channels instead of chasing every trend.",
            "We focus on what moves your KPIs, not vanity metrics.",
        ],
        proof_points=[
            "Clear, channel-wise plans instead of ad-hoc posting.",
            "Consistent brand story across all touchpoints.",
            "Strategy tied back to the goals and constraints you shared.",
        ],
        values=s.brand_adjectives or ["reliable", "consistent", "growth-focused"],
    )

    swot_dict = generate_swot(req.brief)
    swot = SWOTBlock(
        strengths=swot_dict.get("strengths", []),
        weaknesses=swot_dict.get("weaknesses", []),
        opportunities=swot_dict.get("opportunities", []),
        threats=swot_dict.get("threats", []),
    )

    competitor_snapshot = CompetitorSnapshot(
        narrative=(
            "Most brands in this category share similar promises and visuals. "
            "They publish sporadically and rarely build a clear, repeating narrative."
        ),
        common_patterns=[
            "Generic 'quality and service' messaging.",
            "No clear proof or concrete outcomes.",
            "Inconsistent or stagnant social presence.",
        ],
        differentiation_opportunities=[
            "Show concrete outcomes and transformations.",
            "Use simple, repeatable story arcs across content.",
            "Emphasise your unique process and experience.",
        ],
    )

    # Marketing Plan
    mp = MarketingPlanView(
        executive_summary=(
            f"{b.brand_name} is aiming to drive {g.primary_goal or 'growth'} "
            f"over the next {g.timeline or 'period'}. This plan covers strategy, "
            "campaign focus, and channel mix."
        ),
        situation_analysis=generate_situation_analysis(req.brief),
        strategy=(
            "Position the brand as the default choice for its niche by combining:\n"
            "- consistent social presence\n"
            "- proof-driven storytelling (testimonials, case studies)\n"
            "- clear, repeated core promises across all touchpoints."
        ),
        pillars=generate_messaging_pillars(req.brief),
        messaging_pyramid=messaging_pyramid,
        swot=swot,
        competitor_snapshot=competitor_snapshot,
    )

    # Campaign blueprint
    big_idea_industry = b.industry or "your category"
    # Ensure persona label is safe (never a verbatim copy of the goal)
    safe_primary_label = _safe_persona_label(a.primary_customer, g.primary_goal)

    cb = CampaignBlueprintView(
        big_idea=f"Whenever your ideal buyer thinks of {big_idea_industry}, they remember {b.brand_name} first.",
        objective=CampaignObjectiveView(
            primary=g.primary_goal or "brand_awareness",
            secondary=g.secondary_goal,
        ),
        audience_persona=AudiencePersonaView(
            name="Core Buyer",
            description=(
                f"{safe_primary_label} who is actively looking for better options and wants "
                "less friction, more clarity, and trustworthy proof before committing."
            ),
        ),
    )

    # Social calendar - for Quick Social packs we produce a 30-day calendar, otherwise default 7 days
    calendar_days = (
        30
        if (req.package_preset and str(req.package_preset).startswith("quick_social"))
        or (req.wow_package_key and str(req.wow_package_key).startswith("quick_social"))
        else 7
    )

    posts = generate_social_calendar(req.brief, start_date=today, days=calendar_days)

    cal = SocialCalendarView(
        start_date=today,
        end_date=today + timedelta(days=calendar_days - 1),
        posts=posts,
    )

    # Performance review (stub)
    pr: Optional[PerformanceReviewView] = None
    if req.generate_performance_review:
        pr = PerformanceReviewView(
            summary=PerfSummaryView(
                growth_summary="Performance review will be populated once data is available.",
                wins="- Early engagement signals strong message–market resonance.\n",
                failures="- Limited coverage on secondary channels.\n",
                opportunities="- Double down on top performing content themes and formats.\n",
            )
        )

    # Persona cards - brief-driven generation
    # 🔥 FIX #4: Try industry-specific personas first
    if req.generate_personas:
        from backend.industry_config import get_default_personas_for_industry

        industry = req.brief.brand.industry
        industry_personas = get_default_personas_for_industry(industry) if industry else None

        if industry_personas:
            logger.info(f"Using {len(industry_personas)} industry-specific personas for {industry}")
            # Use industry-specific personas (list of dicts compatible with AICMOOutputReport)
            persona_cards = industry_personas
        else:
            # Fallback to generic personas
            logger.debug(f"No industry config for {industry}, using generic personas")
            persona_cards = [generate_persona(req.brief)]
    else:
        persona_cards = [generate_persona(req.brief)]

    # Action plan
    action_plan = ActionPlan(
        quick_wins=[
            "Align the next 7 days of content to the 2–3 key messages defined in this report.",
            "Refresh bio/description on key platforms to reflect the new core promise.",
        ],
        next_10_days=[
            "Publish at least one 'proof' post (testimonial, screenshot, mini case study).",
            "Test one strong offer or lead magnet and track responses.",
        ],
        next_30_days=[
            "Run a focused campaign around one key offer with consistent messaging.",
            "Review content performance and double down on top themes and formats.",
        ],
        risks=[
            "Inconsistent implementation across platforms.",
            "Stopping after initial results instead of compounding further.",
        ],
    )

    # Creatives
    creatives: Optional[CreativesBlock] = None
    if req.generate_creatives:
        core_promise = (
            s.success_30_days
            or f"See visible progress towards {g.primary_goal or 'your goal'} within 30 days."
        )

        rationale = CreativeRationale(
            strategy_summary=(
                "The creative system is built around repeating a few clear promises in multiple "
                "formats. Instagram focuses on visual storytelling, LinkedIn focuses on authority "
                "and proof, while X focuses on sharp, scroll-stopping hooks.\n\n"
                "By reusing the same core ideas across platforms, the brand compounds recognition "
                "instead of starting from scratch each time."
            ),
            psychological_triggers=[
                "Social proof",
                "Loss aversion (fear of missing out on better results)",
                "Clarity and specificity (concrete promises)",
                "Authority and expertise",
            ],
            audience_fit=(
                "Ideal for busy decision-makers who scan feeds quickly but respond strongly to "
                "clear proof and repeated, simple promises."
            ),
            risk_notes=(
                "Avoid over-claiming or using fear-heavy framing; keep promises ambitious but "
                "credible and backed by examples whenever possible."
            ),
        )

        channel_variants = [
            ChannelVariant(
                platform="Instagram",
                format="reel",
                hook=f"Stop guessing your {big_idea_industry} marketing.",
                caption=(
                    f"Most {big_idea_industry} brands post randomly and hope it works.\n\n"
                    f"{b.brand_name} is switching to a simple, repeatable system: "
                    f"{core_promise}\n\n"
                    "Save this if you're done improvising your growth."
                ),
            ),
            ChannelVariant(
                platform="LinkedIn",
                format="post",
                hook=f"What happened when {b.brand_name} stopped 'posting and praying'.",
                caption=(
                    "We replaced random content with a clear playbook: 3 pillars, 2 offers, "
                    "and 1 simple narrative that repeats everywhere.\n\n"
                    "Result: more consistent leads, fewer 'spray and pray' campaigns."
                ),
            ),
            ChannelVariant(
                platform="X",
                format="thread",
                hook="Most brands don't have a marketing problem. They have a focus problem.",
                caption=(
                    "Thread:\n"
                    "1/ They jump from trend to trend.\n"
                    "2/ They never commit to one clear promise.\n"
                    "3/ Their content feels different on every platform.\n\n"
                    "Fix the focus → the metrics follow."
                ),
            ),
        ]

        tone_variants = [
            ToneVariant(
                tone_label="Professional",
                example_caption=(
                    f"{b.brand_name} is implementing a structured, data-aware marketing "
                    "system to replace ad-hoc posting and scattered campaigns."
                ),
            ),
            ToneVariant(
                tone_label="Friendly",
                example_caption=(
                    "No more 'post and pray'. We're building a simple, repeatable marketing "
                    "engine that works even on your busiest weeks."
                ),
            ),
            ToneVariant(
                tone_label="Bold",
                example_caption=(
                    "If your marketing still depends on random ideas and last-minute posts, "
                    "you're leaving serious money on the table."
                ),
            ),
        ]

        email_subject_lines = [
            "Your marketing doesn't need more ideas – it needs a system.",
            f"What happens when {b.brand_name} stops posting randomly?",
            "3 campaigns that can carry your growth for the next 90 days.",
        ]

        hooks = [
            "Stop posting randomly. Start compounding your brand.",
            "Your content is working harder than your strategy. Let's fix that.",
        ]

        captions = [
            "Great marketing is not about doing more. It's about repeating the right things "
            "consistently across channels.",
            "You don't need 100 ideas. You need 5 ideas repeated in 100 smart ways.",
        ]

        scripts = [
            (
                "Opening: Show the chaos (random posts, no clear message).\n"
                "Middle: Introduce the system (3 pillars, 2 offers, 1 narrative).\n"
                "Close: Invite them to take the first step (DM / click / reply)."
            )
        ]

        hook_insights = [
            HookInsight(
                hook=hooks[0],
                insight="Reframes the problem from 'more activity' to 'more compounding', which appeals to strategic buyers.",
            ),
            HookInsight(
                hook=hooks[1],
                insight="Highlights the mismatch between effort and strategy, making the reader feel seen and understood.",
            ),
        ]

        cta_library = [
            CTAVariant(
                label="Soft",
                text="Curious how this could work for you? Reply and we can walk through it.",
                usage_context="Awareness posts, early-stage leads.",
            ),
            CTAVariant(
                label="Medium",
                text="Want the full playbook for your brand? Book a short call.",
                usage_context="Consideration-stage content with proof.",
            ),
            CTAVariant(
                label="Hard",
                text="Ready to stop guessing your marketing? Let's start this week.",
                usage_context="Strong offer posts and end of campaign.",
            ),
        ]

        offer_angles = [
            OfferAngle(
                label="Value angle",
                description="Focus on long-term compounding ROI instead of single-campaign spikes.",
                example_usage="Turn 3 campaigns into a marketing system that keeps working after the campaign ends.",
            ),
            OfferAngle(
                label="Risk-reversal",
                description="Reduce perceived risk by emphasising clarity, structure and support.",
                example_usage="Instead of trying 10 random ideas, run 1 clear, guided playbook for 30 days.",
            ),
        ]

        creatives = CreativesBlock(
            notes="Initial creative system with platform variations, tones, email subjects, CTAs and scripts.",
            hooks=hooks,
            captions=captions,
            scripts=scripts,
            rationale=rationale,
            channel_variants=channel_variants,
            email_subject_lines=email_subject_lines,
            tone_variants=tone_variants,
            hook_insights=hook_insights,
            cta_library=cta_library,
            offer_angles=offer_angles,
        )
    else:
        creatives = None

    # Build extra_sections for package-specific presets
    # This allows WOW templates to reference all sections from the preset
    extra_sections: Dict[str, str] = {}

    if req.package_preset:
        # 🔥 Convert display name to preset key if needed
        preset_key = PACKAGE_NAME_TO_KEY.get(req.package_preset, req.package_preset)
        preset = PACKAGE_PRESETS.get(preset_key)
        if preset:
            # Get the section_ids list from the preset
            section_ids = preset.get("sections", [])

            # 🔥 FIX #2: Apply pack-scoping whitelist
            if req.wow_enabled and req.wow_package_key:
                allowed_sections = get_allowed_sections_for_pack(req.wow_package_key)
                if allowed_sections:
                    original_count = len(section_ids)
                    section_ids = [s for s in section_ids if s in allowed_sections]

                    logger.info(
                        f"Pack scoping applied for {req.wow_package_key}: "
                        f"{original_count} sections → {len(section_ids)} allowed sections"
                    )

                    if len(section_ids) != original_count:
                        filtered_out = set(preset.get("sections", [])) - set(section_ids)
                        logger.debug(f"Filtered out sections: {filtered_out}")

            # Use the generalized generate_sections() function
            extra_sections = generate_sections(
                section_ids=section_ids,
                req=req,
                mp=mp,
                cb=cb,
                cal=cal,
                pr=pr,
                creatives=creatives,
                action_plan=action_plan,
            )

    # 🔥 FIX #8: Normalize persona_cards before instantiation to handle partial LLM-generated personas
    if persona_cards:
        normalised_personas = []
        for p in persona_cards:
            if not isinstance(p, dict):
                continue
            normalised_personas.append(
                {
                    "name": p.get("name") or "Primary Persona",
                    "demographics": p.get("demographics", ""),
                    "psychographics": p.get("psychographics", ""),
                    "tone_preference": p.get("tone_preference", ""),
                    "pain_points": p.get("pain_points", []),
                    "triggers": p.get("triggers", []),
                    "objections": p.get("objections", []),
                    "content_preferences": p.get("content_preferences", []),
                    "primary_platforms": p.get("primary_platforms", []),
                }
            )
        persona_cards = normalised_personas

    out = AICMOOutputReport(
        marketing_plan=mp,
        campaign_blueprint=cb,
        social_calendar=cal,
        performance_review=pr,
        creatives=creatives,
        persona_cards=persona_cards,
        action_plan=action_plan,
        extra_sections=extra_sections,
    )
    return out


def _apply_wow_to_output(
    output: AICMOOutputReport,
    req: GenerateRequest,
) -> AICMOOutputReport:
    """
    Optional WOW template wrapping using the new WOW system.

    If wow_enabled=True and wow_package_key is provided:
    - Fetches WOW rule structure (with sections) for the package
    - Builds a complete WOW report using the section assembly
    - Stores in wow_markdown field
    - Stores package_key for reference
    - Applies humanization layer for style improvement (non-breaking)

    Non-breaking: if WOW fails or is disabled, output is returned unchanged.
    """
    # 🔥 DIAGNOSTIC LOGGING: Track fallback decision
    logger.info(
        "FALLBACK_DECISION_START",
        extra={
            "wow_enabled": req.wow_enabled,
            "wow_package_key": req.wow_package_key,
            "will_apply_wow": bool(req.wow_enabled and req.wow_package_key),
        },
    )

    if not req.wow_enabled or not req.wow_package_key:
        fallback_reason = ""
        if not req.wow_enabled:
            fallback_reason = "wow_enabled=False"
        elif not req.wow_package_key:
            fallback_reason = "wow_package_key is None/empty"

        logger.info(
            "FALLBACK_DECISION_RESULT",
            extra={"fallback_reason": fallback_reason, "action": "SKIP_WOW_FALLBACK_TO_STUB"},
        )
        return output

    try:
        # Fetch the WOW rule for this package (contains section structure)
        wow_rule = get_wow_rule(req.wow_package_key)
        sections = wow_rule.get("sections", [])

        # 🔥 DIAGNOSTIC LOGGING: Log WOW package and sections
        logger.info(
            "WOW_PACKAGE_RESOLUTION",
            extra={
                "wow_package_key": req.wow_package_key,
                "sections_found": len(sections),
                "section_keys": [s.get("key") for s in sections],
            },
        )

        # Debug: Log which WOW pack and sections are being used
        if len(sections) == 0:
            logger.warning(
                "WOW_PACKAGE_EMPTY_SECTIONS",
                extra={
                    "wow_package_key": req.wow_package_key,
                    "action": "FALLBACK_TO_STUB",
                    "reason": "WOW rule has empty sections list",
                },
            )
            # No sections defined for this package - return stub output
            return output

        print(f"[WOW DEBUG] Using WOW pack: {req.wow_package_key}")
        print(f"[WOW DEBUG] Sections in WOW rule: {[s['key'] for s in sections]}")

        # Build the WOW report using the new unified system
        wow_markdown = build_wow_report(req=req, wow_rule=wow_rule)

        # Apply humanization layer: light style cleanup, no structural changes
        try:
            industry_key = (
                getattr(req.brief, "industry_key", None) or getattr(req.brief, "industry", "") or ""
            )
        except Exception:
            industry_key = ""

        try:
            industry_profile = get_industry_config(industry_key) if industry_key else None
            industry_profile_dict = dict(industry_profile) if industry_profile else {}
        except Exception:
            industry_profile_dict = {}

        # Determine humanization level based on pack type
        pack_humanize_level = "light"
        if req.wow_package_key in {
            "strategy_campaign_standard",
            "full_funnel_growth_suite",
            "launch_gtm_pack",
        }:
            pack_humanize_level = "medium"

        try:
            humanizer_config = HumanizerConfig(level=pack_humanize_level)
            wow_markdown = humanize_report_text(
                wow_markdown,
                brief=req.brief,
                pack_key=req.wow_package_key,
                industry_key=str(industry_key),
                config=humanizer_config,
                industry_profile=industry_profile_dict,
            )
            logger.debug(
                f"Humanization applied to {req.wow_package_key} (level={pack_humanize_level})"
            )
        except Exception as e:
            logger.debug(f"Humanization failed (non-breaking): {e}")
            # Continue without humanization

        # Store in output
        output.wow_markdown = wow_markdown
        output.wow_package_key = req.wow_package_key

        logger.info(
            "WOW_APPLICATION_SUCCESS",
            extra={
                "wow_package_key": req.wow_package_key,
                "sections_count": len(sections),
                "action": "WOW_APPLIED_SUCCESSFULLY",
            },
        )
        logger.debug(f"WOW report built successfully: {req.wow_package_key}")
        logger.info(f"WOW system used {len(sections)} sections for {req.wow_package_key}")

        # 🔥 PHASE 1: Validate pack contract after WOW report is built
        try:
            from backend.validators.output_validator import validate_pack_contract

            validate_pack_contract(req.wow_package_key, output)
            logger.info(f"✅ Pack contract validation passed for {req.wow_package_key}")
        except ValueError as ve:
            logger.warning(f"⚠️  Pack contract validation failed for {req.wow_package_key}: {ve}")
            # Non-breaking: log warning but don't fail report generation
        except Exception as e:
            logger.debug(f"Pack contract validation error (non-critical): {e}")

        # 🔥 PHASE 2: Validate section quality against benchmarks
        try:
            from backend.validators.report_gate import validate_report_sections

            # Prepare sections for validation (convert from output format)
            validation_sections = [
                {"id": s["id"], "content": s["content"]}
                for s in sections
                if isinstance(s, dict) and "id" in s and "content" in s
            ]

            if validation_sections:
                validation_result = validate_report_sections(
                    pack_key=req.wow_package_key, sections=validation_sections
                )

                logger.info(
                    f"✅ Benchmark validation completed for {req.wow_package_key}: "
                    f"status={validation_result.status}, "
                    f"sections={len(validation_result.section_results)}, "
                    f"issues={sum(len(r.issues) for r in validation_result.section_results)}"
                )

                # If validation fails, log detailed error summary
                if validation_result.status in ["FAIL", "PASS_WITH_WARNINGS"]:
                    error_summary = validation_result.get_error_summary()
                    if validation_result.status == "FAIL":
                        logger.warning(
                            f"⚠️  Quality gate FAILED for {req.wow_package_key}:\n{error_summary}"
                        )
                    else:
                        logger.info(
                            f"ℹ️  Quality warnings for {req.wow_package_key}:\n{error_summary}"
                        )

                    # Optional: Store validation results in output for debugging
                    # You could add a new field to output object to track quality issues
            else:
                logger.debug("No sections available for benchmark validation")

        except Exception as e:
            logger.warning(
                f"Benchmark validation error (non-critical) for {req.wow_package_key}: {e}"
            )
            # Non-breaking: log warning but don't fail report generation

    except Exception as e:
        logger.warning(
            "WOW_APPLICATION_FAILED",
            extra={
                "wow_package_key": req.wow_package_key,
                "error": str(e),
                "exception_type": type(e).__name__,
                "action": "FALLBACK_TO_STUB",
            },
        )
        # Non-breaking: continue without WOW

    return output


def _retrieve_learning_context(brief_text: str) -> tuple[str, dict]:
    """
    Retrieve relevant learning context from memory database.

    Args:
        brief_text: Text representation of client brief

    Returns:
        Tuple of (raw_context_string, structured_framework_dict)
    """
    try:
        raw_context = memory_engine.retrieve_relevant_context(
            prompt_text=brief_text,
            top_k=20,
        )
        if not raw_context:
            logger.debug("Phase L: No learning context retrieved")
            return "", {}

        structured = structure_learning_context(raw_context)
        logger.info(
            f"Phase L: Retrieved and structured learning context ({len(raw_context)} chars)"
        )
        return raw_context, structured
    except Exception as e:
        logger.warning(f"Phase L: Learning context retrieval failed (non-critical): {e}")
        return "", {}


@app.post("/aicmo/generate", response_model=AICMOOutputReport)
async def aicmo_generate(req: GenerateRequest) -> AICMOOutputReport:
    """
    Public endpoint for AICMO generation.

    1. Always builds a deterministic stub output (CI-safe, offline).
    2. If AICMO_USE_LLM=1:
         → Uses LLM generators (marketing plan, etc.)
         → Passes through the LLM enhancement layer with industry presets
       Otherwise:
         → Returns the stub as-is.
    3. Auto-records output as a learning example (always, non-blocking).
    4. If include_agency_grade=True: applies agency-grade turbo enhancements.
    """
    # ═══════════════════════════════════════════════════════════════════════
    # DEBUG: Learning system status
    # ═══════════════════════════════════════════════════════════════════════
    if req.model_dump().get("use_learning", False):
        logger.info("🔥 [LEARNING ENABLED] use_learning flag received from Streamlit")
    else:
        logger.info("⚠️  [LEARNING DISABLED] use_learning=False or missing")

    # Check if LLM should be used
    use_llm = os.getenv("AICMO_USE_LLM", "0") == "1"

    if use_llm:
        try:
            # Use LLM to generate marketing plan
            marketing_plan = await generate_marketing_plan(req.brief)
            base_output = _generate_stub_output(req)
            # Update with LLM-generated marketing plan
            base_output.marketing_plan = marketing_plan
        except Exception as e:
            logger.warning(f"LLM marketing plan generation failed, using stub: {e}", exc_info=False)
            base_output = _generate_stub_output(req)
    else:
        # Default: offline & deterministic (current behaviour)
        base_output = _generate_stub_output(req)

    if not use_llm:
        # Default: offline & deterministic (current behaviour)
        # But still try to record learning (non-blocking)
        try:
            record_learning_from_output(
                brief=req.brief, output=base_output.model_dump(), notes="Auto-recorded stub output"
            )
        except Exception as e:
            logger.debug(f"Learning recording failed (non-critical): {e}")

        # Phase L: Retrieve and apply learning context if enabled
        learning_context_raw = ""
        learning_context_struct = {}
        if req.use_learning:
            brief_text = str(
                req.brief.model_dump() if hasattr(req.brief, "model_dump") else req.brief
            )
            learning_context_raw, learning_context_struct = _retrieve_learning_context(brief_text)

        # TURBO: Apply agency-grade enhancements if requested and enabled
        turbo_enabled = os.getenv("AICMO_TURBO_ENABLED", "1") == "1"
        if req.include_agency_grade and turbo_enabled:
            try:
                apply_agency_grade_enhancements(req.brief, base_output)

                # Phase L: Process for agency-grade (frameworks + language filters)
                brief_text = str(
                    req.brief.model_dump() if hasattr(req.brief, "model_dump") else req.brief
                )
                base_output = process_report_for_agency_grade(
                    report=base_output,
                    brief_text=brief_text,
                    learning_context_raw=learning_context_raw,
                    learning_context_struct=learning_context_struct,
                    include_reasoning_trace=True,  # Internal review only
                )
                logger.info("Phase L: Agency-grade processing complete (frameworks + filters)")

            except Exception as e:
                logger.debug(f"Agency-grade enhancements failed (non-critical): {e}")

        # Optionally attach reasoning trace for internal review
        if req.include_agency_grade and learning_context_raw:
            try:
                # Note: attach_reasoning_trace is for markdown/internal, not applied to structured output
                logger.debug("Phase L: Reasoning trace available for internal review")
            except Exception as e:
                logger.debug(f"Reasoning trace attachment failed (non-critical): {e}")

        # Phase L: Auto-learn from this final report (gated by AICMO_ENABLE_HTTP_LEARNING)
        # Import quality gate check
        from backend.quality_gates import is_report_learnable

        if AICMO_ENABLE_HTTP_LEARNING:
            try:
                # Check report quality before learning
                report_text = generate_output_report_markdown(req.brief, base_output)
                is_learnable, reasons = is_report_learnable(
                    report_text, brief_brand_name=req.brief.brand.brand_name
                )

                if is_learnable:
                    learn_from_report(
                        report=base_output,
                        project_id=None,  # No explicit project ID in this context
                        tags=["auto_learn", "final_report"],
                    )
                    logger.info("🔥 [LEARNING RECORDED] Report learned and stored in memory engine")
                else:
                    logger.warning(
                        "⚠️  [LEARNING SKIPPED] Report failed quality gate: %s", "; ".join(reasons)
                    )
            except Exception as e:
                logger.debug(f"Auto-learning failed (non-critical): {e}")
                logger.warning("⚠️  [LEARNING FAILED] Report could not be recorded: %s", str(e))
        else:
            logger.info(
                "ℹ️  [HTTP LEARNING] Disabled (AICMO_ENABLE_HTTP_LEARNING=0). Skipping learn_from_report."
            )

        # WOW: Apply optional template wrapping
        base_output = _apply_wow_to_output(base_output, req)

        # 🔥 FIX #6: Validate output before export
        try:
            from backend.validators import OutputValidator

            validator = OutputValidator(
                output=base_output,
                brief=req.brief,
                wow_package_key=req.wow_package_key if req.wow_enabled else None,
            )
            issues = validator.validate_all()

            error_count = sum(1 for i in issues if i.severity == "error")
            if error_count > 0 and req.wow_enabled:
                logger.warning(f"Output validation: {error_count} blocking issues detected")
                logger.debug(validator.get_error_summary())
        except Exception as e:
            logger.debug(f"Output validation failed (non-critical): {e}")

        return base_output

    # LLM mode – best-effort polish with industry presets + learning, never breaks the endpoint
    try:
        # Phase L: Retrieve learning context early in LLM path
        learning_context_raw = ""
        learning_context_struct = {}
        if req.use_learning:
            brief_text = str(
                req.brief.model_dump() if hasattr(req.brief, "model_dump") else req.brief
            )
            learning_context_raw, learning_context_struct = _retrieve_learning_context(brief_text)

        # Phase 5: Use enhanced LLM layer with industry presets + learning
        enhanced = enhance_with_llm_new(
            brief=req.brief,
            stub_output=base_output.model_dump(),
            options={"industry_key": req.industry_key},
        )

        # Convert enhanced dict back to AICMOOutputReport
        enhanced_output = AICMOOutputReport.model_validate(enhanced)

        # TURBO: Apply agency-grade enhancements if requested and enabled
        turbo_enabled = os.getenv("AICMO_TURBO_ENABLED", "1") == "1"
        if req.include_agency_grade and turbo_enabled:
            try:
                apply_agency_grade_enhancements(req.brief, enhanced_output)

                # Phase L: Process for agency-grade (frameworks + language filters)
                brief_text = str(
                    req.brief.model_dump() if hasattr(req.brief, "model_dump") else req.brief
                )
                enhanced_output = process_report_for_agency_grade(
                    report=enhanced_output,
                    brief_text=brief_text,
                    learning_context_raw=learning_context_raw,
                    learning_context_struct=learning_context_struct,
                    include_reasoning_trace=True,  # Internal review only
                )
                logger.info("Phase L: Agency-grade processing complete (frameworks + filters)")

            except Exception as e:
                logger.debug(f"Agency-grade enhancements failed (non-critical): {e}")

        # Phase 5: Auto-record this enhanced output as a learning example
        try:
            record_learning_from_output(
                brief=req.brief,
                output=enhanced_output.model_dump(),
                notes=f"LLM-enhanced output (industry: {req.industry_key or 'none'})",
            )
        except Exception as e:
            logger.debug(f"Learning recording failed (non-critical): {e}")

        # Phase L: Auto-learn from this final report (gated by AICMO_ENABLE_HTTP_LEARNING)
        if AICMO_ENABLE_HTTP_LEARNING:
            try:
                learn_from_report(
                    report=enhanced_output,
                    project_id=None,  # No explicit project ID in this context
                    tags=["auto_learn", "final_report", "llm_enhanced"],
                )
                logger.info(
                    "🔥 [LEARNING RECORDED] LLM-enhanced report learned and stored in memory engine"
                )
            except Exception as e:
                logger.debug(f"Auto-learning failed (non-critical): {e}")
                logger.warning("⚠️  [LEARNING FAILED] Report could not be recorded: %s", str(e))
        else:
            logger.info(
                "ℹ️  [HTTP LEARNING] Disabled (AICMO_ENABLE_HTTP_LEARNING=0). Skipping learn_from_report."
            )

        # WOW: Apply optional template wrapping
        enhanced_output = _apply_wow_to_output(enhanced_output, req)

        return enhanced_output
    except RuntimeError as e:
        # LLM SDK missing etc. – log and fall back quietly
        logger.info(f"LLM disabled or not installed: {e}")

        # TURBO: Apply agency-grade enhancements if requested and enabled (even on fallback)
        turbo_enabled = os.getenv("AICMO_TURBO_ENABLED", "1") == "1"
        if req.include_agency_grade and turbo_enabled:
            try:
                apply_agency_grade_enhancements(req.brief, base_output)
            except Exception as e:
                logger.debug(f"Agency-grade enhancements failed (non-critical): {e}")

        # Phase L: Auto-learn from this final report (even on fallback, gated by AICMO_ENABLE_HTTP_LEARNING)
        if AICMO_ENABLE_HTTP_LEARNING:
            try:
                learn_from_report(
                    report=base_output,
                    project_id=None,
                    tags=["auto_learn", "final_report", "llm_fallback"],
                )
                logger.info(
                    "🔥 [LEARNING RECORDED] Fallback report learned and stored in memory engine"
                )
            except Exception as e:
                logger.debug(f"Auto-learning failed (non-critical): {e}")
                logger.warning("⚠️  [LEARNING FAILED] Report could not be recorded: %s", str(e))
        else:
            logger.info(
                "ℹ️  [HTTP LEARNING] Disabled (AICMO_ENABLE_HTTP_LEARNING=0). Skipping learn_from_report."
            )

        # WOW: Apply optional template wrapping
        base_output = _apply_wow_to_output(base_output, req)

        return base_output
    except Exception as e:
        # Any unexpected LLM error – do NOT break operator flow
        logger.error(f"LLM enhancement failed, falling back to stub: {e}", exc_info=True)

        # TURBO: Apply agency-grade enhancements if requested and enabled (even on fallback)
        turbo_enabled = os.getenv("AICMO_TURBO_ENABLED", "1") == "1"
        if req.include_agency_grade and turbo_enabled:
            try:
                apply_agency_grade_enhancements(req.brief, base_output)
            except Exception as e:
                print(f"[AICMO] Agency-grade enhancements failed (non-critical): {e}")

        # Phase L: Auto-learn from this final report (even on fallback, gated by AICMO_ENABLE_HTTP_LEARNING)
        if AICMO_ENABLE_HTTP_LEARNING:
            try:
                learn_from_report(
                    report=base_output,
                    project_id=None,
                    tags=["auto_learn", "final_report", "llm_fallback"],
                )
            except Exception as e:
                print(f"[AICMO] Auto-learning failed (non-critical): {e}")
        else:
            print(
                "[AICMO] HTTP learning disabled (AICMO_ENABLE_HTTP_LEARNING=0). Skipping learn_from_report."
            )

        # WOW: Apply optional template wrapping
        base_output = _apply_wow_to_output(base_output, req)

        return base_output


# =====================================================================
# SCHEMA VALIDATION HELPERS – Ensure briefs are always complete
# =====================================================================

REQUIRED_BRIEF_FIELDS = [
    "brand_name",
    "industry",
    "product_service",
    "primary_goal",
    "primary_customer",
]


def validate_client_brief(brief: "ClientInputBrief") -> None:
    """
    Validate that a ClientInputBrief has all required fields populated.
    Raises HTTPException if any required field is missing or empty.
    """
    from fastapi import HTTPException

    missing: list[str] = []

    # Check brand fields
    if not brief.brand.brand_name or not brief.brand.brand_name.strip():
        missing.append("brand_name")
    if not brief.brand.industry or not brief.brand.industry.strip():
        missing.append("industry")
    if not brief.brand.product_service or not brief.brand.product_service.strip():
        missing.append("product_service")

    # Check goal fields
    if not brief.goal.primary_goal or not brief.goal.primary_goal.strip():
        missing.append("primary_goal")

    # Check audience fields
    if not brief.audience.primary_customer or not brief.audience.primary_customer.strip():
        missing.append("primary_customer")

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing or empty required fields: {', '.join(missing)}",
        )


@app.post("/api/aicmo/generate_report")
async def api_aicmo_generate_report(payload: dict) -> dict:
    """
    Streamlit-compatible wrapper endpoint for /aicmo/generate.

    Converts Streamlit's payload structure to GenerateRequest and calls the core endpoint.
    Expected Streamlit payload format:
    {
        "stage": "draft|refine|final",
        "client_brief": {
            "raw_brief_text": "...",
            "client_name": "...",
            "brand_name": "...",
            "product_service": "...",
            "industry": "...",
            "geography": "...",
            "objectives": "...",
            "budget": "...",
            "timeline": "...",
            "constraints": "..."
        },
        "services": {...dict with include_agency_grade, wow_enabled, etc...},
        "package_name": "Strategy + Campaign Pack (Standard)",
        "wow_enabled": bool,
        "wow_package_key": str or None,
        "refinement_mode": {...},
        "feedback": str,
        "previous_draft": str,
        "learn_items": [...],
        "use_learning": bool,
        "industry_key": str or None,
    }

    Returns:
    {
        "report_markdown": "...markdown content...",
        "status": "success"
    }
    """
    try:
        # Extract top-level payload fields
        package_name = payload.get("package_name")
        stage = payload.get("stage", "draft")
        services = payload.get("services", {})
        client_brief_dict = payload.get("client_brief", {})
        wow_enabled = payload.get("wow_enabled", False)
        wow_package_key = payload.get("wow_package_key")
        use_learning = payload.get("use_learning", False)
        industry_key = payload.get("industry_key")
        refinement_mode = payload.get("refinement_mode", {})

        include_agency_grade = services.get("include_agency_grade", False)

        # 🔥 FIX #3️⃣: Convert display name to preset_key using PACKAGE_NAME_TO_KEY mapping
        resolved_preset_key = PACKAGE_NAME_TO_KEY.get(package_name, package_name)
        logger.info(f"🔥 [PRESET MAPPING] {package_name} → {resolved_preset_key}")

        # BUILD COMPLETE ClientInputBrief from flattened Streamlit payload
        # This is THE KEY FIX: construct ALL required nested structures with sensible defaults
        from aicmo.io.client_reports import (
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

        # Build ClientInputBrief from payload — be explicit about which payload keys map to which fields.
        # IMPORTANT: Never use the primary_goal text as a fallback for persona/audience fields.
        primary_goal_val = (
            client_brief_dict.get("primary_goal", "").strip()
            or client_brief_dict.get("objectives", "").strip()
            or "Achieve your business goal"
        )

        primary_customer_val = (
            client_brief_dict.get("primary_customer", "").strip()
            or client_brief_dict.get("primary_audience", "").strip()
            or "ideal customers"
        )

        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name=client_brief_dict.get("brand_name", "").strip() or "Your Brand",
                industry=client_brief_dict.get("industry", "").strip() or "your industry",
                product_service=client_brief_dict.get("product_service", "").strip()
                or "your main product/service",
                primary_goal=primary_goal_val,
                primary_customer=primary_customer_val,
                location=client_brief_dict.get("geography", "").strip() or None,
                timeline=client_brief_dict.get("timeline", "").strip() or None,
                business_type=client_brief_dict.get("business_type", "").strip() or None,
                description=client_brief_dict.get("product_service", "").strip() or None,
            ),
            audience=AudienceBrief(
                primary_customer=primary_customer_val,
                pain_points=client_brief_dict.get("pain_points", []) or [],
            ),
            goal=GoalBrief(
                primary_goal=primary_goal_val,
                timeline=client_brief_dict.get("timeline", "").strip() or None,
                kpis=client_brief_dict.get("kpis", []) or [],
            ),
            voice=VoiceBrief(tone_of_voice=[]),
            product_service=ProductServiceBrief(
                items=(
                    [
                        ProductServiceItem(
                            name=client_brief_dict.get("product_service", "").strip()
                            or "Your Product/Service",
                            usp=None,
                        )
                    ]
                    if client_brief_dict.get("product_service")
                    else []
                )
            ),
            assets_constraints=AssetsConstraintsBrief(
                focus_platforms=[],
            ),
            operations=OperationsBrief(
                needs_calendar=True,
            ),
            strategy_extras=StrategyExtrasBrief(
                brand_adjectives=[],
                success_30_days=None,
            ),
        )

        # Apply safe defaults to prevent downstream errors
        brief = brief.with_safe_defaults()

        # Validate that required fields are present
        validate_client_brief(brief)

        # 🔥 FIX #2️⃣: Compute effective_stage for Strategy + Campaign Pack (Standard)
        # This ensures the standard pack always drives a FULL, final-style report
        # even if the incoming stage is "draft"
        if (
            package_name == "Strategy + Campaign Pack (Standard)"
            and include_agency_grade
            and wow_enabled
            and wow_package_key == "strategy_campaign_standard"
        ):
            effective_stage = "final"
            logger.info(
                "🔥 [STANDARD PACK] Forcing effective_stage='final' for full report generation"
            )
        else:
            effective_stage = stage

        # 🔥 FIX #4️⃣: Force safe token ceiling for Standard pack
        if (
            package_name == "Strategy + Campaign Pack (Standard)"
            and include_agency_grade
            and wow_enabled
        ):
            original_max_tokens = refinement_mode.get("max_tokens", 6000)
            refinement_mode["max_tokens"] = max(original_max_tokens, 12000)
            logger.info(
                f"🔥 [STANDARD PACK] Token limit enforced: "
                f"{original_max_tokens} → {refinement_mode['max_tokens']}"
            )

        # Force 2-pass refinement for quality
        refinement_mode["passes"] = 2

        # Build GenerateRequest using SAME structure as tests
        gen_req = GenerateRequest(
            brief=brief,
            generate_marketing_plan=services.get("marketing_plan", True),
            generate_campaign_blueprint=services.get("campaign_blueprint", True),
            generate_social_calendar=services.get("social_calendar", True),
            generate_performance_review=services.get("performance_review", False),
            generate_creatives=services.get("creatives", True),
            package_preset=resolved_preset_key,  # 🔥 FIX #3: Use resolved preset key
            include_agency_grade=include_agency_grade,
            use_learning=use_learning,
            wow_enabled=wow_enabled,
            wow_package_key=wow_package_key,
            industry_key=industry_key,
            stage=effective_stage,  # 🔥 FIX #2: Use effective_stage
        )

        # Call the SAME core generator function that tests use
        report = await aicmo_generate(gen_req)

        # Convert output to markdown
        report_markdown = generate_output_report_markdown(brief, report)

        # 🔥 FIX #5: Apply final sanitization pass to remove placeholders
        from aicmo.generators.language_filters import sanitize_final_report_text

        report_markdown = sanitize_final_report_text(report_markdown)
        logger.info("✅ [SANITIZER] Applied final report sanitization pass")

        # 🔍 DEBUG: Add diagnostics footer to report (if AICMO_DEBUG_REPORT_FOOTER env var is set)
        import os

        if os.getenv("AICMO_DEBUG_REPORT_FOOTER"):
            # Count sections in the report by looking for section headers
            section_count = report_markdown.count("## ")
            # Extract list of section IDs from the report
            import re

            section_ids = re.findall(r"^## (.+)$", report_markdown, re.MULTILINE)

            diagnostics_footer = (
                f"\n\n---\n\n### DEBUG FOOTER (HTTP ENDPOINT PATH)\n"
                f"- **Preset Key**: {resolved_preset_key}\n"
                f"- **Display Name**: {package_name}\n"
                f"- **Original Stage**: {stage}\n"
                f"- **Effective Stage**: {effective_stage}\n"
                f"- **WOW Enabled**: {wow_enabled}\n"
                f"- **WOW Package Key**: {wow_package_key}\n"
                f"- **Effective Max Tokens**: {refinement_mode.get('max_tokens', 'unknown')}\n"
                f"- **Sections in Report**: {section_count}\n"
                f"- **Report Length**: {len(report_markdown)} chars\n"
            )
            if section_ids:
                diagnostics_footer += f"- **Section IDs**: {', '.join(section_ids[:20])}\n"
            report_markdown += diagnostics_footer
            logger.info("🔥 [DIAGNOSTICS] Added debug footer to HTTP endpoint response")

        logger.info(
            f"✅ [HTTP ENDPOINT] generate_report successful. "
            f"preset={resolved_preset_key}, stage={effective_stage}, "
            f"include_agency_grade={include_agency_grade}, length={len(report_markdown)}"
        )

        return {
            "report_markdown": report_markdown,
            "status": "success",
        }
    except HTTPException:
        # Already handled (from llm_client or other handlers)
        raise
    except Exception as e:
        logger.exception("Unhandled error in /api/aicmo/generate_report: %s", type(e).__name__)
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {type(e).__name__}: {str(e)[:100]}"
        )


@app.get("/aicmo/industries")
def list_industries():
    """Phase 5: List available industry presets."""
    return {
        "industries": list_available_industries(),
        "description": "Industry presets for content generation guidance",
    }


@app.post("/aicmo/revise", response_model=AICMOOutputReport)
async def aicmo_revise(
    meta: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
):
    """
    Revision stub:
    - Reads brief + current_output + instructions from 'meta' JSON.
    - For now, just appends a note to the executive summary so you see a change.
    - Phase 5: Auto-records revised output as a learning example.
    """
    try:
        data = json.loads(meta)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid meta JSON")

    current = AICMOOutputReport.model_validate(data["current_output"])

    # Make a shallow copy and tweak executive summary
    mp = current.marketing_plan
    revised_mp = MarketingPlanView(
        executive_summary=mp.executive_summary
        + "\n\n_Revision note: updated according to operator feedback._",
        situation_analysis=mp.situation_analysis,
        strategy=mp.strategy,
        pillars=mp.pillars,
    )

    revised = current.model_copy(update={"marketing_plan": revised_mp})

    # Phase 5: Try to record revised output (non-blocking)
    try:
        brief = ClientInputBrief.model_validate(data.get("brief", {}))
        record_learning_from_output(
            brief=brief, output=revised.model_dump(), notes="Auto-recorded revised output"
        )
    except Exception as e:
        logger.debug(f"Learning recording failed (non-critical): {e}")

    return revised


@app.post("/api/competitor/research")
async def api_competitor_research(payload: dict):
    """
    Lightweight wrapper around competitor_finder for Streamlit UI.

    Accepts payload with industry, location, pincode, and other fields.
    Returns list of competitors or error (non-fatal).
    """
    try:
        industry = payload.get("industry") or payload.get("category")
        location = payload.get("location") or payload.get("city")
        pincode = payload.get("pincode") or payload.get("zipcode")

        if not industry or not location:
            return {
                "status": "error",
                "error": "industry and location required",
                "competitors": [],
            }

        competitors = find_competitors_for_brief(
            business_category=industry,
            location=location,
            pincode=pincode,
            limit=10,
        )

        return {"status": "ok", "competitors": competitors or []}
    except Exception as exc:
        logger.warning(f"Competitor research failed (non-fatal): {exc}")
        return {
            "status": "error",
            "error": str(exc),
            "competitors": [],
        }


@app.post("/aicmo/export/pdf")
def aicmo_export_pdf(payload: dict):
    """
    Convert markdown or structured sections to PDF with safe error handling.

    Supports three modes:
    1. Agency-grade PDF: { "wow_enabled": True, ... }
    2. Markdown mode: { "markdown": "..." }
    3. Structured mode: { "sections": [...], "brief": {...} }

    Returns:
        StreamingResponse with PDF on success (Content-Type: application/pdf).
        JSONResponse with error details on failure (Content-Type: application/json).
    """
    try:
        # Check if agency-grade PDF export is enabled
        wow_enabled = payload.get("wow_enabled", False)

        if wow_enabled:
            try:
                logger.info("🎨 [AGENCY PDF] Attempting agency-grade PDF export...")
                return safe_export_agency_pdf(payload)
            except Exception as e:
                logger.warning(
                    f"🎨 [AGENCY PDF] Agency export failed, falling back to standard: {e}"
                )
                # Fall through to standard export

        # Mode 1: Try structured sections first (HTML template rendering)
        sections = payload.get("sections")
        brief = payload.get("brief")

        if sections and brief:
            try:
                # Build context for template
                context = {
                    "client_name": brief.get("client_name") or "Client",
                    "brand_name": brief.get("brand_name") or "Brand",
                    "product_service": brief.get("product_service") or "",
                    "location": brief.get("location") or "",
                    "campaign_duration": brief.get("campaign_duration") or "",
                    "prepared_by": brief.get("prepared_by") or "AICMO",
                    "date": brief.get("date_str") or str(date.today()),
                    "sections": sections_to_html_list(sections),
                    "show_contents": True,
                }

                pdf_bytes = render_pdf_from_context(
                    template_name="strategy_campaign_standard.html",
                    context=context,
                )

                # Validate PDF header (double-check)
                if not pdf_bytes.startswith(b"%PDF"):
                    raise ValueError("Renderer did not produce a valid PDF stream")

                logger.info(f"PDF exported via structured mode: {len(pdf_bytes)} bytes")
                return StreamingResponse(
                    iter([pdf_bytes]),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": 'attachment; filename="AICMO_Marketing_Plan.pdf"'
                    },
                )
            except Exception as e:
                logger.debug(f"Structured PDF rendering failed (not fatal): {e}")
                # Fall through to markdown mode

        # Mode 2: Fallback to markdown mode
        markdown = payload.get("markdown") or ""

        # If no markdown and no valid structured data, return error
        if not markdown:
            logger.warning("PDF export: no markdown or structured sections provided")
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "PDF export requires either 'markdown' or 'sections' + 'brief' data.",
                    "export_type": "pdf",
                },
            )

        result = safe_export_pdf(markdown, check_placeholders=True)

        # If result is a dict, it's an error – return as JSON
        if isinstance(result, dict):
            logger.warning(f"PDF export failed: {result}")
            return JSONResponse(status_code=400, content=result)

        # Otherwise, it's a StreamingResponse – return it
        logger.info("PDF exported via markdown mode")
        return result

    except Exception as e:
        logger.error(f"PDF export endpoint error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": f"PDF export failed: {str(e)}",
                "export_type": "pdf",
            },
        )


@app.post("/aicmo/export/pptx")
def aicmo_export_pptx(payload: dict):
    """
    Convert brief + output to PPTX with safe error handling.

    Body: { "brief": {...}, "output": {...} }

    Returns:
        StreamingResponse with PPTX on success.
        JSONResponse with error details on failure.
    """
    try:
        brief = ClientInputBrief.model_validate(payload["brief"])
        output = AICMOOutputReport.model_validate(payload["output"])
    except Exception as e:
        logger.error(f"PPTX export: invalid input validation: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "message": "Invalid brief or output format.",
                "export_type": "pptx",
            },
        )

    result = safe_export_pptx(brief, output)

    # If result is a dict, it's an error – return as JSON
    if isinstance(result, dict):
        logger.warning(f"PPTX export failed: {result}")
        return JSONResponse(status_code=400, content=result)

    # Otherwise, it's a StreamingResponse – return it
    return result


@app.post("/aicmo/export/zip")
def aicmo_export_zip(payload: dict):
    """
    Export a ZIP with report, personas, creatives with safe error handling.

    Body: { "brief": {...}, "output": {...} }

    Returns:
        StreamingResponse with ZIP on success.
        JSONResponse with error details on failure.
    """
    try:
        brief = ClientInputBrief.model_validate(payload["brief"])
        output = AICMOOutputReport.model_validate(payload["output"])
    except Exception as e:
        logger.error(f"ZIP export: invalid input validation: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "message": "Invalid brief or output format.",
                "export_type": "zip",
            },
        )

    result = safe_export_zip(brief, output)

    # If result is a dict, it's an error – return as JSON
    if isinstance(result, dict):
        logger.warning(f"ZIP export failed: {result}")
        return JSONResponse(status_code=400, content=result)

    # Otherwise, it's a StreamingResponse – return it
    return result
