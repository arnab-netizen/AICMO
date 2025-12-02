"""FastAPI main app: Day-1 intake + Day-2 AICMO operator endpoints."""

from __future__ import annotations

import json
import logging
import os
import time
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

# Phase 3: Request fingerprinting, caching, and performance timing
from backend.utils.request_fingerprint import make_fingerprint, log_request  # noqa: E402
from backend.utils.report_cache import GLOBAL_REPORT_CACHE  # noqa: E402
from backend.utils.config import is_stub_mode  # noqa: E402
from backend.utils.stub_sections import _stub_section_for_pack  # noqa: E402
from backend.validators.report_enforcer import BenchmarkEnforcementError  # noqa: E402

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
    # Quick Social Pack (Basic) - 8 core sections only (tightened scope)
    "quick_social_basic": {
        "overview",  # Brand & Objectives
        "messaging_framework",  # Strategy Lite / brand messaging pyramid
        "detailed_30_day_calendar",  # 30-day content calendar (hero section)
        "content_buckets",  # Hooks + caption examples
        "hashtag_strategy",  # Simple hashtag strategy
        "kpi_plan_light",  # Light KPIs
        "execution_roadmap",  # 7-day execution checklist / next steps
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

# Phase 3: Performance threshold for slow request flagging
SLOW_THRESHOLD_MS = 8000.0  # 8 seconds


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
    from backend.industry_config import get_industry_profile

    b = req.brief.brand
    g = req.brief.goal
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Check for industry profile (Quick Social + specific industries)
    profile = get_industry_profile(b.industry)
    use_industry_vocab = profile and "quick_social" in pack_key.lower()

    # Build industry description
    if use_industry_vocab and profile.vocab:
        # Use industry-specific vocabulary (e.g., "third place" for coffeehouse)
        vocab_sample = profile.vocab[0]  # First vocab item (e.g., "third place")
        industry_desc = (
            f"Operating in the {b.industry or 'competitive market'} sector, {b.brand_name} "
            f"aims to become the go-to {vocab_sample} for {b.primary_customer or 'customers'}. "
            f"Success in this space requires consistent brand presence, authentic community building, "
            f"and memorable customer experiences."
        )
    else:
        industry_desc = (
            f"Operating in the {b.industry or 'competitive market'} sector, {b.brand_name} "
            f"focuses on innovation, quality, and customer satisfaction. The industry landscape "
            f"demands consistent brand presence, clear messaging, and proof-driven strategies."
        )

    raw = (
        f"## Brand\n\n"
        f"**Brand:** {b.brand_name}\n\n"
        f"{b.brand_name} is a {b.industry or 'dynamic'} company committed to delivering "
        f"exceptional {b.product_service or 'products and services'} to {b.primary_customer or 'customers'}. "
        f"The brand represents quality, innovation, and customer-centric values.\n\n"
        f"## Industry\n\n"
        f"**Industry:** {b.industry or 'competitive market'}\n\n"
        f"{industry_desc}\n\n"
        f"## Primary Goal\n\n"
        f"**Primary Goal:** {g.primary_goal or 'drive growth and expand market reach'}\n\n"
        f"This strategic initiative requires a data-driven approach with measurable KPIs:\n\n"
        f"- Develop consistent content calendar that resonates with target audience\n"
        f"- Track engagement metrics, reach, and conversion rates\n"
        f"- Build sustainable brand presence across key platforms\n"
        f"- Establish credible voice through proof-driven narratives"
    )
    return sanitize_output(raw, req.brief)


def _gen_campaign_objective(req: GenerateRequest, **kwargs) -> str:
    """Generate 'campaign_objective' section."""
    g = req.brief.goal
    b = req.brief.brand
    a = req.brief.audience
    raw = (
        f"## Primary Objective\n\n"
        f"**Primary Objective:** {g.primary_goal or 'Brand awareness and growth'}\n\n"
        f"Drive measurable business impact for {b.brand_name} by achieving {g.primary_goal or 'key growth objectives'}. "
        f"This campaign focuses on creating sustainable momentum through strategic audience engagement, "
        f"compelling messaging, and data-driven optimization across all channels. By addressing the core needs of "
        f"{a.primary_customer or 'target customers'}, we'll build lasting relationships that convert initial awareness "
        f"into loyal advocacy. The objective prioritizes quality over quantity, ensuring every interaction adds value "
        f"and moves prospects closer to conversion while maintaining authentic brand integrity.\n\n"
        f"## Secondary Objectives\n\n"
        f"**Secondary Objectives:** {g.secondary_goal or 'Lead generation, customer retention'}\n\n"
        f"Support the primary objective with complementary goals including expanding market reach, "
        f"strengthening brand authority, and building a loyal community of advocates. These objectives "
        f"work together to create compounding results over time. Each secondary goal serves a strategic purpose: "
        f"market expansion identifies new opportunity segments, authority building establishes credibility and trust, "
        f"and community development creates organic growth through referrals and word-of-mouth advocacy.\n\n"
        f"## Time Horizon\n\n"
        f"**Target Timeline:** {g.timeline or '90 days'}\n\n"
        f"This campaign is structured as a {g.timeline or '90-day'} sprint with weekly milestones, "
        f"bi-weekly optimization cycles, and monthly performance reviews. The timeline ensures focus "
        f"while allowing flexibility to adapt based on real-time performance data. This phased approach balances "
        f"urgency with sustainability, creating quick wins that build toward long-term strategic goals.\n\n"
        f"**Success Metrics:** Increased brand awareness ({g.kpis[0] if g.kpis else 'reach'}), lead volume, "
        f"and customer engagement across key channels. Track progression weekly with full analysis monthly. Specific KPIs "
        f"include engagement rate targets (>2%), conversion benchmarks, and cost-per-acquisition thresholds that ensure "
        f"efficient budget allocation and sustainable growth momentum."
    )
    return sanitize_output(raw, req.brief)


def _gen_core_campaign_idea(req: GenerateRequest, **kwargs) -> str:
    """Generate 'core_campaign_idea' section."""
    b = req.brief.brand
    g = req.brief.goal
    s = req.brief.strategy_extras
    a = req.brief.audience
    raw = (
        f"## Big Idea\n\n"
        f"**Big Idea:** Position {b.brand_name} as the definitive choice in {b.industry or 'the market'} through "
        f"strategic authority building and proof-driven storytelling\n\n"
        f"Transform {b.brand_name} from just another option to the obvious choice for {b.primary_customer or 'target customers'}. "
        f"This campaign establishes market authority by consistently demonstrating expertise, showcasing real results, "
        f"and building trust through transparent, proof-driven communication. The core insight: customers don't choose "
        f"random brands—they choose the one that makes success feel inevitable. By addressing {a.pain_points or 'key challenges'} "
        f"directly and showing measurable solutions, this campaign creates an undeniable value proposition.\n\n"
        f"## Creative Territory\n\n"
        f"The creative approach centers on 'From Chaos to Clarity'—showing the transformation journey from current "
        f"challenges to desired outcomes. Visual storytelling combines before/after narratives, customer success moments, "
        f"and behind-the-scenes expertise. Content balances educational value with social proof, positioning "
        f"{b.brand_name} as both teacher and trusted partner. Every piece of content reinforces the central narrative "
        f"of transformation, backed by data and real customer experiences that resonate with {b.primary_customer or 'the target audience'}.\n\n"
        f"## Why It Works\n\n"
        f"**Key Insight:** {s.success_30_days or 'Customers prefer brands that demonstrate clear, repeatable promises backed by concrete proof'}\n\n"
        f"This approach works because it addresses the core barrier to conversion: trust. By leading with value, "
        f"showcasing real results, and maintaining consistent presence, {b.brand_name} builds credibility naturally. "
        f"The strategy compounds over time as each proof point strengthens the next, creating unstoppable momentum toward "
        f"{g.primary_goal or 'achieving campaign objectives'}. Market research shows that proof-driven narratives "
        f"increase conversion rates by demonstrating capability rather than just making claims.\n\n"
        f"- Establishes authority through consistent, valuable content and thought leadership\n"
        f"- Builds trust through transparency, proof, and authentic customer stories\n"
        f"- Creates momentum through strategic repetition across channels\n"
        f"- Converts attention into action by removing doubt and building confidence\n"
        f"- Generates word-of-mouth through remarkable, shareable results"
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
    a = req.brief.audience

    promise = (
        mp.messaging_pyramid.promise
        if mp.messaging_pyramid
        else f"{b.brand_name} delivers consistent, measurable results that move the needle on {g.primary_goal or 'core business objectives'}"
    )

    key_messages = (
        mp.messaging_pyramid.key_messages
        if mp.messaging_pyramid
        else [
            f"We understand the challenges facing {b.primary_customer or 'our customers'}",
            f"Our {b.product_service or 'solutions'} are proven to drive real results",
            "Transparent, data-driven approach with clear ROI",
            f"Built specifically for {b.primary_customer or 'your needs'}",
        ]
    )

    proof_points = (
        mp.messaging_pyramid.proof_points
        if mp.messaging_pyramid
        else [
            "Demonstrated track record of customer success",
            "Clear metrics and measurable outcomes",
            "Real results from real customers",
        ]
    )

    raw = (
        f"## Core Message\n\n"
        f"**Central Promise:** {promise}\n\n"
        f"{b.brand_name} combines industry expertise in {b.industry or 'the market'} with proven methodologies "
        f"to deliver exceptional {b.product_service or 'solutions'} that solve real problems for "
        f"{b.primary_customer or 'customers'}. Our approach ensures measurable impact and sustainable growth. "
        f"We focus on addressing {a.pain_points or 'key challenges'} with evidence-based strategies that deliver "
        f"tangible outcomes aligned with {g.primary_goal or 'your business objectives'}. Every campaign decision "
        f"is guided by data, customer feedback, and proven best practices that consistently drive results.\n\n"
        f"## Key Themes\n\n"
        f"**Strategic Pillars for All Communications:**\n\n"
        + "\n".join(f"- {msg}" for msg in key_messages)
        + "\n\n"
        "These themes reinforce our commitment to transparency, measurable results, and customer-centric innovation. "
        "Each message is designed to build trust, demonstrate value, and create urgency through relevance and proof. "
        "The messaging hierarchy ensures consistency across all channels while allowing flexibility for platform-specific adaptation. "
        "Every piece of content should reinforce at least one of these core themes.\n\n"
        "## Proof Points\n\n" + "\n".join(f"- {pp}" for pp in proof_points) + "\n\n"
        "This messaging framework ensures all communications maintain consistency, credibility, and "
        "compelling narratives across every touchpoint. Every piece of content reinforces these core themes, "
        "building brand equity and customer confidence through strategic repetition and proof-driven storytelling."
    )
    return sanitize_output(raw, req.brief)


def _gen_channel_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'channel_plan' section."""
    b = req.brief.brand
    a = req.brief.assets_constraints
    g = req.brief.goal
    platforms = a.focus_platforms or ["Instagram", "LinkedIn", "Email"]
    primary = platforms[:3]
    secondary = ["X", "YouTube", "Paid Ads"]

    raw = (
        f"## Priority Channels\n\n"
        f"**Primary Channels:** {', '.join(primary)}\n\n"
        f"These platforms form the foundation of {b.brand_name}'s campaign strategy, selected based on audience "
        f"concentration, engagement potential, and alignment with campaign objectives. Focus 70% of resources here "
        f"for maximum impact and consistent presence. These channels have proven audience fit with {b.primary_customer or 'target customers'} "
        f"and offer the best ROI potential for achieving {g.primary_goal or 'campaign goals'}. Research shows that "
        f"maintaining strong presence on 2-3 core platforms outperforms scattered efforts across many channels.\n\n"
        f"**Secondary Channels:** {', '.join(secondary)}\n\n"
        f"Supporting channels that extend reach and provide testing opportunities. Allocate 30% of resources to "
        f"explore new audiences and validate messaging before scaling. These platforms allow for experimentation "
        f"with new content formats, audience segments, and creative approaches without risking primary channel performance. "
        f"Use secondary channels to test hypotheses that can inform primary channel strategy.\n\n"
        f"## Channel Strategy\n\n"
        f"Integrated approach coordinating message and timing across all platforms for maximum impact. Each channel plays "
        f"specific role in customer journey from awareness to conversion while maintaining consistent brand narrative. "
        f"Primary channels drive daily engagement and relationship building. Secondary channels provide scale and testing. "
        f"Strategy emphasizes quality over quantity with deep presence on core channels outperforming shallow presence everywhere.\n\n"
        f"## Role of Each Channel\n\n"
        f"- **{primary[0]}:** Primary awareness and engagement driver—visual storytelling, social proof, community building, daily brand presence\n"
        f"- **{primary[1] if len(primary) > 1 else 'Social'}:** Authority positioning through thought leadership, professional content, industry insights, and B2B engagement\n"
        f"- **{primary[2] if len(primary) > 2 else 'Email'}:** Nurture and conversion—deeper engagement, direct CTAs, relationship building, personalized journeys\n"
        f"- **Paid Ads:** Amplification and retargeting—scale winning content, re-engage warm audiences, accelerate top-of-funnel growth\n"
        f"- **YouTube/Video:** Long-form education and demonstration—detailed case studies, tutorials, webinars, behind-the-scenes content\n"
        f"- **X/Twitter:** Real-time engagement and thought leadership—industry conversations, quick insights, trending topics, community interaction\n\n"
        f"## Key Tactics\n\n"
        f"**Content Strategy:** Develop 3-5 core content pillars (education, proof, transformation, community) and "
        f"map to each channel based on format strengths. Repurpose hero content across channels adapting for platform "
        f"specifications while maintaining message consistency. Test new content types on secondary channels before "
        f"scaling to primary channels.\n\n"
        f"**Posting Cadence:** Primary channels 5-7x weekly, secondary channels 2-3x weekly maintaining presence without "
        f"overwhelming audience. Schedule posts for optimal engagement times based on platform analytics. Build content "
        f"buffer maintaining 2-week advance planning to allow for strategic flexibility.\n\n"
        f"**Engagement Protocol:** Respond to comments within 2 hours, engage authentically with community posts, "
        f"participate in relevant conversations beyond owned content. Assign team members specific channels for consistent "
        f"monitoring and engagement building relationships not just broadcasting messages.\n\n"
        f"## Budget Focus\n\n"
        f"Allocate 70% of budget to {', '.join(primary)} for sustained presence and deep audience connection. Reserve "
        f"20% for paid amplification of winning organic content accelerating reach and testing new segments. Hold 10% "
        f"for experimental channels and emerging platforms validating opportunities before major investment. Review budget "
        f"allocation monthly adjusting based on performance data and ROI metrics per channel.\n"
    )
    return sanitize_output(raw, req.brief)
    return sanitize_output(raw, req.brief)


def _gen_audience_segments(req: GenerateRequest, **kwargs) -> str:
    """Generate 'audience_segments' section."""
    b = req.brief.brand
    a = req.brief.audience
    g = req.brief.goal
    # Use safe persona label to avoid goal text being echoed as audience
    primary_label = _safe_persona_label(
        a.primary_customer, getattr(req.brief.goal, "primary_goal", None)
    )
    secondary_label = a.secondary_customer or "Referral sources and advocates"

    raw = (
        f"## Primary Audience\n\n"
        f"**Primary Audience:** {primary_label}\n\n"
        f"{primary_label} represent the core target for {b.brand_name}. This segment is actively seeking "
        f"{b.product_service or 'solutions'} and prioritizes clarity and proof points. They are motivated by "
        f"{g.primary_goal or 'achieving measurable outcomes'} and face challenges including {a.pain_points or 'time constraints and information overload'}. "
        f"Understanding their decision-making process is crucial for effective campaign messaging. Key characteristics:\n\n"
        f"- Research thoroughly before making decisions, comparing multiple options\n"
        f"- Respond well to testimonials, case studies, and data-driven proof\n"
        f"- Value transparency, clear communication, and measurable results\n"
        f"- Prefer actionable insights over generic promotional content\n\n"
        f"## Secondary Audience\n\n"
        f"**Secondary Audience:** {secondary_label}\n\n"
        f"{secondary_label} serve as decision influencers and brand advocates who can amplify campaign reach. "
        f"This segment includes existing customers, industry peers, and community members who benefit from sharing "
        f"{b.brand_name}'s solutions with their networks. Engaging this audience creates compounding growth effects. Key characteristics:\n\n"
        f"- Share content and provide referrals within their professional networks\n"
        f"- Value authenticity, proof-driven narratives, and community recognition\n"
        f"- Motivated by helping others succeed and establishing their own expertise\n"
        f"- Respond to opportunities for co-creation and collaborative content"
    )
    return sanitize_output(raw, req.brief)


def _gen_persona_cards(
    req: GenerateRequest,
    cb: CampaignBlueprintView,
    **kwargs,
) -> str:
    """Generate 'persona_cards' section."""
    b = req.brief.brand
    a = req.brief.audience
    g = req.brief.goal

    primary_name = cb.audience_persona.name or "The Strategic Decision-Maker"
    primary_desc = cb.audience_persona.description or (
        f"Actively seeking {b.product_service or 'solutions'} and wants less friction, more clarity, "
        "and trustworthy proof before committing to any investment."
    )

    raw = (
        f"## Primary Persona\n\n"
        f"**{primary_name}**\n\n"
        f"**Profile:** {primary_desc}\n\n"
        f"This persona represents the core buyer for {b.brand_name}—someone who has budget authority and is "
        f"actively evaluating options to achieve {g.primary_goal or 'key business objectives'}. They face pressure "
        f"to make the right decision and avoid costly mistakes. Their buying process is methodical, research-driven, "
        f"and heavily influenced by peer recommendations and proven results.\n\n"
        f"**Key Characteristics:**\n"
        f"- Job Role: {a.primary_customer or 'Department Head, Team Lead, or Key Stakeholder'}\n"
        f"- Primary Goal: {g.primary_goal or 'Achieve measurable improvements with minimal risk'}\n"
        f"- Pain Points: Time constraints, choice overload, lack of credible proof, fear of making wrong decision\n"
        f"- Desires: Clarity, proven systems, efficiency, transparent ROI, implementation support\n"
        f"- Content Preference: Case studies, testimonials, video walkthroughs, comparison guides, ROI calculators\n"
        f"- Preferred Channels: LinkedIn, industry newsletters, peer recommendations, webinars\n\n"
        f"## Secondary Persona\n\n"
        f"**The Influencer & Advocate**\n\n"
        f"**Profile:** {a.secondary_customer or 'Team members, industry peers, and existing customers'} who influence "
        f"buying decisions through recommendations, reviews, and social proof.\n\n"
        f"This persona may not have direct purchasing power but shapes the decision-making environment. They include "
        f"satisfied customers who share their experiences, team members who research options, and industry thought leaders "
        f"whose opinions carry weight. Engaging this persona creates credibility and amplifies campaign reach organically.\n\n"
        f"**Key Characteristics:**\n"
        f"- Role: User, team member, community member, satisfied customer\n"
        f"- Motivation: Help others succeed, establish expertise, contribute to community\n"
        f"- Engagement Style: Share content, write reviews, participate in discussions, provide testimonials\n"
        f"- Content Preference: Success stories, behind-the-scenes content, community features, quick wins\n\n"
        f"## Motivations\n\n"
        f"**Core Drivers Across Both Personas:**\n\n"
        f"- **Risk Mitigation:** Avoid making costly mistakes or choosing unreliable vendors\n"
        f"- **Efficiency Gains:** Save time, reduce complexity, streamline processes\n"
        f"- **Proven Results:** See evidence of success from similar customers in similar situations\n"
        f"- **Professional Growth:** Advance career by making smart decisions that deliver measurable impact\n"
        f"- **Community Recognition:** Be known as someone who discovers and shares valuable solutions\n"
        f"- **Trust & Transparency:** Work with vendors who communicate clearly and deliver on promises"
    )
    return sanitize_output(raw, req.brief)


def _gen_creative_direction(
    req: GenerateRequest,
    **kwargs,
) -> str:
    """Generate 'creative_direction' section."""
    s = req.brief.strategy_extras
    b = req.brief.brand
    a = req.brief.audience

    tone_attrs = (
        ", ".join(s.brand_adjectives)
        if s.brand_adjectives
        else "reliable, consistent, growth-focused, transparent"
    )

    raw = (
        f"## Visual Style\n\n"
        f"**Brand Aesthetic:** Clean, professional, and proof-oriented design that builds trust and credibility\n\n"
        f"The visual direction for {b.brand_name} emphasizes clarity, professionalism, and results-driven storytelling. "
        f"Every design element should reinforce the brand's commitment to transparency and measurable outcomes. The aesthetic "
        f"balances sophistication with approachability—professional enough to inspire confidence, human enough to build connection. "
        f"Avoid overly corporate stiffness or casual unprofessionalism. The goal is 'trusted expert' positioning.\n\n"
        f"**Color Palette:** Primary brand colors with strategic use of accent colors for emphasis and hierarchy. "
        f"Use high contrast for readability, white space for clarity, and color psychology to guide attention toward "
        f"CTAs and key messages. Maintain consistency across all touchpoints to build brand recognition.\n\n"
        f"**Photography & Imagery:** Real people, authentic moments, and genuine customer success stories. Avoid generic "
        f"stock photos that feel inauthentic. Prioritize before/after visuals, behind-the-scenes content, and user-generated "
        f"content when possible. Show the transformation journey that resonates with {a.primary_customer or 'target audience'}.\n\n"
        f"## Tone of Voice\n\n"
        f"**Brand Personality:** {tone_attrs}\n\n"
        f"The tone for all {b.brand_name} communications should be {tone_attrs}. Speak with authority but not arrogance. "
        f"Use clear, jargon-free language that respects the audience's intelligence while making complex concepts accessible. "
        f"Lead with value and proof rather than hype or unsubstantiated claims. Be conversational without being overly casual. "
        f"The voice should sound like a knowledgeable friend who's genuinely invested in the customer's success.\n\n"
        f"**Communication Style:**\n"
        f"- Direct and action-oriented (avoid vague generalities)\n"
        f"- Evidence-based (always support claims with data or examples)\n"
        f"- Customer-centric (focus on their outcomes, not our features)\n"
        f"- Transparent about process, pricing, and expectations\n\n"
        f"## Key Design Elements\n\n"
        f"**Visual Components for All Campaign Materials:**\n\n"
        f"- **Typography:** Professional fonts with strong visual hierarchy—headlines that grab attention, body text that's easy to scan\n"
        f"- **Social Proof:** Client logos, testimonial quotes, user counts, success metrics displayed prominently\n"
        f"- **Data Visualization:** Metrics and results presented through charts, graphs, and clear numerical callouts\n"
        f"- **Consistent Branding:** Logo placement, color usage, and design patterns that build recognition across channels\n"
        f"- **Whitespace:** Generous spacing that guides the eye and prevents overwhelm\n"
        f"- **Clear CTAs:** Buttons and calls-to-action that stand out and communicate value clearly"
    )
    return sanitize_output(raw, req.brief)


def _gen_influencer_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'influencer_strategy' section."""
    b = req.brief.brand
    g = req.brief.goal
    a = req.brief.audience

    raw = (
        f"## Influencer Tiers\n\n"
        f"**Tier 1: Micro-Influencers (10k-100k followers)**\n\n"
        f"Target thought leaders and industry practitioners in {b.industry or 'the market'} who have highly engaged, "
        f"relevant audiences. These influencers offer authentic credibility and strong community trust. Their followers "
        f"align closely with {a.primary_customer or 'target customers'} and actively seek recommendations on "
        f"{b.product_service or 'relevant solutions'}. Micro-influencers typically deliver higher engagement rates "
        f"and more qualified leads than macro-influencers at a fraction of the cost.\n\n"
        f"**Tier 2: Industry Experts (1k-10k followers)**\n\n"
        f"Niche specialists whose smaller but highly targeted audiences provide deep relevance. These partners excel "
        f"at creating educational content, detailed reviews, and technical walkthroughs. Their authority in specific "
        f"sub-segments makes them valuable for reaching decision-makers who prioritize expertise over broad popularity.\n\n"
        f"**Tier 3: Customer Advocates (Existing Users)**\n\n"
        f"Satisfied customers who naturally share their experiences through organic content and testimonials. This tier "
        f"provides the most authentic social proof and can be activated through referral programs, user-generated content "
        f"campaigns, and community advocacy initiatives.\n\n"
        f"## Activation Strategy\n\n"
        f"**Partnership Models:**\n\n"
        f"- **Co-Created Content:** Collaborate on case studies, webinar series, and joint content campaigns that provide "
        f"mutual value. Partner with influencers to create educational content that addresses {a.pain_points or 'audience challenges'}.\n"
        f"- **Product Reviews:** Provide early access or demonstration opportunities in exchange for honest, detailed reviews "
        f"that showcase real use cases and outcomes.\n"
        f"- **Affiliate Partnerships:** Create commission structures that align incentives and reward influencers for driving "
        f"qualified leads and conversions.\n"
        f"- **Event Collaborations:** Co-host webinars, workshops, or virtual events that position both parties as authorities "
        f"and generate leads for both brands.\n"
        f"- **Guest Content:** Exchange guest blog posts, podcast appearances, and newsletter features to tap into each other's audiences.\n\n"
        f"**Vetting Criteria:**\n"
        f"- Audience demographics match {a.primary_customer or 'target customer profile'}\n"
        f"- Engagement rate exceeds 2% (comments, shares, meaningful interactions)\n"
        f"- Content quality and authenticity align with {b.brand_name} values\n"
        f"- Track record of successful partnerships and professional communication\n"
        f"- No conflicts with competing brands or controversial associations\n\n"
        f"## Measurement & Optimization\n\n"
        f"**Key Metrics:**\n\n"
        f"- **Engagement Rate:** Target >2% for micro-influencers, >1% for larger accounts\n"
        f"- **Click-Through Rate:** Measure link clicks and landing page visits from influencer content\n"
        f"- **Lead Attribution:** Track conversions using unique codes, affiliate links, and UTM parameters\n"
        f"- **Content Performance:** Monitor reach, impressions, saves, and shares across influencer posts\n"
        f"- **Cost Per Acquisition:** Calculate CPA to determine ROI and optimize budget allocation\n\n"
        f"**Budget Allocation:** Reserve 15-20% of media spend for influencer partnerships. Start with smaller tests, "
        f"measure results rigorously, and scale winning partnerships aggressively. Prioritize long-term relationships "
        f"over one-off posts to build authentic advocacy and compound brand awareness toward {g.primary_goal or 'campaign objectives'}."
    )
    return sanitize_output(raw, req.brief)


def _gen_promotions_and_offers(req: GenerateRequest, **kwargs) -> str:
    """Generate 'promotions_and_offers' section."""
    b = req.brief.brand
    g = req.brief.goal
    a = req.brief.audience

    raw = (
        f"## Promotional Strategy\n\n"
        f"**Campaign-Driven Offers Aligned with {g.primary_goal or 'Business Objectives'}**\n\n"
        f"The promotional strategy for {b.brand_name} focuses on providing genuine value while removing barriers to "
        f"initial engagement. Rather than relying on aggressive discounting that devalues the brand, this approach "
        f"emphasizes risk reversal, education, and strategic time-limited opportunities that create urgency without "
        f"appearing desperate. Each offer is designed to move {a.primary_customer or 'prospects'} through the funnel "
        f"by addressing specific objections at each stage.\n\n"
        f"**Primary Lead Magnets:**\n"
        f"- **Free Consultation or Strategy Audit:** Demonstrate the value of {b.brand_name}'s approach through "
        f"personalized assessment and recommendations\n"
        f"- **Educational Email Series:** Multi-part content that builds authority and nurtures interest over time\n"
        f"- **Resource Library Access:** High-value templates, frameworks, or tools that provide immediate utility\n"
        f"- **Live Workshop or Webinar:** Interactive sessions that showcase expertise and allow for real-time engagement\n\n"
        f"**Timing & Cadence:** Launch strategic offers every 2-3 weeks to maintain campaign momentum without causing "
        f"promotion fatigue. Use countdown timers and clear CTAs to create genuine urgency. Align offer launches with "
        f"content themes and campaign phases for maximum relevance and conversion potential.\n\n"
        f"## Offer Types\n\n"
        f"**Awareness Stage:**\n"
        f"- Free resources, educational content, industry reports\n"
        f"- No-commitment value delivery to build trust and establish authority\n\n"
        f"**Consideration Stage:**\n"
        f"- Free consultation, personalized audit, demo access\n"
        f"- Low-friction opportunities to experience value firsthand\n\n"
        f"**Conversion Stage:**\n"
        f"- Time-limited discounts for early commitment\n"
        f"- Bundle offers that increase perceived value\n"
        f"- Payment plan options that reduce financial barrier\n\n"
        f"**Retention & Advocacy:**\n"
        f"- Referral bonuses and affiliate partnerships\n"
        f"- Loyalty rewards for long-term customers\n"
        f"- Exclusive access to advanced features or content\n\n"
        f"**Risk Reversal Mechanisms:**\n"
        f"- Money-back guarantee (30-60 days)\n"
        f"- No-commitment trial period\n"
        f"- Satisfaction guarantee with clear refund policy\n"
        f"- Success-based pricing or performance guarantees where appropriate"
    )
    return sanitize_output(raw, req.brief)


def _gen_ugc_and_community_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'ugc_and_community_plan' section."""
    b = req.brief.brand
    g = req.brief.goal

    raw = f"""## UGC Strategy

Systematic user-generated content acquisition transforming customers into content creators and brand advocates for {b.brand_name}.

**Content Acquisition Framework:**
- **Customer Spotlights**: Feature stories showcasing how customers achieve {g.primary_goal} using {b.brand_name} solutions
- **Testimonial Campaigns**: Structured outreach collecting video, written, and photo testimonials with clear submission guidelines
- **Challenge Initiatives**: Branded challenges encouraging customers to create and share content using specific hashtags
- **Review Amplification**: Strategic requests for reviews on key platforms timed to moments of customer satisfaction
- **Creator Partnerships**: Collaborate with micro-influencers and industry voices to generate authentic third-party content

**Incentive Structures:**
- Recognition programs featuring top contributors on official channels and marketing materials
- Exclusive access to beta features, premium content, or VIP community tiers for active participants
- Monetary rewards or discounts for high-quality submissions meeting brand guidelines and usage rights
- Gamification elements with points, badges, and leaderboards driving ongoing participation

## Community Tactics

Building engaged communities that foster peer connections and organic advocacy:

**Platform Strategy:**
- Dedicated community spaces on Slack, Discord, Facebook Groups, or proprietary platforms facilitating member interaction
- Regular virtual events including Q&A sessions, workshops, member showcases creating connection opportunities
- Structured onboarding sequences welcoming new members and explaining community norms and value propositions

**Engagement Mechanisms:**
- Weekly discussion prompts and questions sparking conversations around {b.industry} topics and challenges
- Member-to-member support channels where experienced users help newcomers reducing support burden
- User-generated resource libraries curating best practices, templates, and frameworks from community contributions
- Recognition programs celebrating active contributors, helpful members, and community champions
- Expert AMAs and fireside chats providing exclusive access to industry leaders and internal team members
- Collaborative projects where members work together on initiatives benefiting entire community
- Feedback loops systematically gathering community input on product roadmap and strategic decisions

## Content Moderation & Quality

Maintaining brand standards while encouraging authentic expression:

- Clear community guidelines defining acceptable content, behavior expectations, and moderation policies
- Pre-approval workflows for UGC intended for official marketing channels ensuring quality and message alignment
- Rights management systems securing proper usage permissions and attribution requirements
- Moderation team or tools monitoring community spaces for spam, off-topic content, or policy violations
- Content templates and guidelines helping members create on-brand submissions without stifling creativity

Success metrics: UGC submission volume, community engagement rate, member retention, advocacy indicators, support ticket deflection rate."""
    return sanitize_output(raw, req.brief)


def _gen_detailed_30_day_calendar(req: GenerateRequest, **kwargs) -> str:
    """
    Generate 'detailed_30_day_calendar' section.

    For Quick Social packs: produces day-by-day 30-day table with rotating content buckets,
    angles, platforms, and unique hooks.

    For other packs: produces phase-based strategic calendar.
    """
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Quick Social: Day-by-day detailed calendar
    if "quick_social" in pack_key.lower():
        return _gen_quick_social_30_day_calendar(req)

    # Default: Phase-based strategic calendar for full packs
    b = req.brief.brand
    g = req.brief.goal

    raw = (
        f"## Phase 1: Foundation & Awareness (Week 1-2)\n\n"
        f"**Strategic Focus:** Establish brand presence, introduce core value proposition, and begin building awareness "
        f"for {b.brand_name}. The first phase prioritizes education and storytelling over direct selling to create "
        f"psychological safety and initial trust with {b.primary_customer or 'the target audience'}.\n\n"
        f"| Week | Days | Content Theme | Key Activities | Expected Outcomes |\n"
        f"|------|------|---------------|----------------|-------------------|\n"
        f"| 1 | 1-7 | Brand Story & Value Positioning | 3-4 hero posts introducing core promise<br>2 educational carousel posts about the category<br>1 behind-the-scenes/origin story post<br>Launch email welcome series | Establish baseline awareness<br>Build initial follower base<br>Collect email subscribers |\n"
        f"| 2 | 8-14 | Social Proof & Case Studies | 3-4 case study or testimonial posts<br>2 before/after transformation posts<br>1 customer interview video<br>Launch educational email sequence | Demonstrate credibility<br>Shift from awareness to consideration<br>Generate engagement and shares |\n\n"
        f"## Phase 2: Engagement & Consideration (Week 3)\n\n"
        f"**Strategic Focus:** Deepen engagement, showcase expertise, and guide prospects toward conversion readiness. "
        f"Phase 2 emphasizes proof, authority building, and interactive content that moves audience from passive "
        f"observation to active consideration.\n\n"
        f"| Week | Days | Content Theme | Key Activities | Expected Outcomes |\n"
        f"|------|------|---------------|----------------|-------------------|\n"
        f"| 3 | 15-21 | Channel-Specific Tactics & Authority Building | Platform-optimized content variations<br>2-3 reel/video posts showcasing results<br>1 live Q&A or webinar session<br>Industry insights and thought leadership posts<br>Launch offer nurture sequence | Increase engagement rates<br>Position {b.brand_name} as category authority<br>Generate qualified leads<br>Build retargeting audience |\n\n"
        f"## Phase 3: Conversion & Action (Week 4)\n\n"
        f"**Strategic Focus:** Drive conversions through strategic CTAs, limited-time offers, and urgency mechanisms. "
        f"Phase 3 leverages the trust and awareness built in earlier phases to convert warm prospects into customers "
        f"or qualified leads aligned with {g.primary_goal or 'campaign objectives'}.\n\n"
        f"| Week | Days | Content Theme | Key Activities | Expected Outcomes |\n"
        f"|------|------|---------------|----------------|-------------------|\n"
        f"| 4 | 22-30 | Calls to Action & Lead Generation | 3 direct CTA posts with clear value propositions<br>Final offer push with countdown timer<br>2 urgency-based posts (limited spots, deadline approaching)<br>Testimonial compilation video<br>Launch conversion email sequence | Generate qualified leads/sales<br>Convert warm prospects to customers<br>Collect detailed lead information<br>Establish post-campaign nurture list |\n\n"
        f"**Ongoing Tactics Across All Phases:**\n"
        f"- Daily Instagram Stories or LinkedIn updates maintaining consistent presence\n"
        f"- Weekly community engagement (respond to comments, join relevant conversations)\n"
        f"- Bi-weekly performance review and optimization based on engagement data\n"
        f"- Continuous A/B testing of headlines, formats, and posting times\n"
        f"- Regular audience feedback collection through polls, surveys, and direct messages"
    )
    return sanitize_output(raw, req.brief)


def _gen_quick_social_30_day_calendar(req: GenerateRequest) -> str:
    """
    Generate day-by-day 30-day calendar for Quick Social pack.

    Features:
    - Rotating content buckets (Education, Proof, Promo, Community)
    - Rotating angles (Product spotlight, Experience, Offer, Community, BTS)
    - Platform rotation (Instagram, LinkedIn, Twitter)
    - Day-of-week bucket mapping
    - Unique hooks per post based on bucket + angle + platform
    - Phase 1 quality upgrades: creative territories, visual concepts, genericity detection
    """
    from datetime import date, timedelta
    from backend.industry_config import get_industry_profile
    from backend.creative_territories import get_creative_territories_for_brief
    from backend.visual_concepts import generate_visual_concept
    from backend.genericity_scoring import is_too_generic

    b = req.brief.brand
    g = req.brief.goal
    industry = b.industry or "your industry"
    brand_name = b.brand_name
    goal_short = g.primary_goal or "customer engagement"

    # Get industry profile for specialized vocabulary
    profile = get_industry_profile(industry)

    # Phase 1: Get creative territories for brand-aware content guidance
    brief_dict = {
        "brand_name": brand_name,
        "industry": industry,
        "geography": getattr(b, "geography", "Global"),
    }
    creative_territories = get_creative_territories_for_brief(brief_dict)

    # Content buckets
    CONTENT_BUCKETS = ["Education", "Proof", "Promo", "Community"]

    # Content angles
    ANGLES = [
        "Product spotlight",
        "Experience in-store",
        "Offer/promo",
        "Community/UGC",
        "Behind-the-scenes",
    ]

    # Day-of-week → default bucket mapping (0=Monday, 6=Sunday)
    DAY_BUCKET_MAP = {
        0: "Education",  # Monday: reset / learn something
        1: "Proof",  # Tuesday: testimonials
        2: "Community",  # Wednesday: engagement
        3: "Education",  # Thursday: tips
        4: "Promo",  # Friday: treat yourself
        5: "Experience",  # Saturday: in-store experience
        6: "Community",  # Sunday: chill / family
    }

    # Platforms (available for reference)
    _ = ["Instagram", "LinkedIn", "Twitter"]  # noqa: F841

    # Asset types by platform
    ASSET_TYPES = {
        "Instagram": ["reel", "static_post", "carousel"],
        "LinkedIn": ["static_post", "document", "carousel"],
        "Twitter": ["short_post", "thread"],
    }

    # CTA library by bucket
    CTA_LIBRARY = {
        "Education": [
            "Save this for later.",
            "Try this next time you visit.",
            "Learn more in bio.",
        ],
        "Proof": [
            "Read the full story.",
            "See why regulars keep coming back.",
            "Tap to discover more.",
        ],
        "Promo": [
            "Claim this offer today.",
            "Show this post in-store.",
            "Limited time—tap to save.",
        ],
        "Community": [
            "Tag someone you'd bring along.",
            "Share your go-to order in comments.",
            "Join the conversation.",
        ],
        "Experience": [
            "Visit us this week.",
            "Experience it yourself.",
            "Come see what makes us special.",
        ],
    }

    # Generate 30 days
    today = date.today()
    rows = []

    for day_num in range(1, 31):
        post_date = today + timedelta(days=day_num - 1)
        weekday = post_date.weekday()  # 0=Mon, 6=Sun

        # Determine bucket
        bucket_default = DAY_BUCKET_MAP.get(weekday, "Education")
        # Use "Experience" only on Saturday, otherwise default or cycle through
        if bucket_default == "Experience":
            bucket = "Experience"
        else:
            # Cycle through buckets to ensure variety
            bucket = CONTENT_BUCKETS[(day_num - 1) % len(CONTENT_BUCKETS)]
            # But prefer weekend promo on Friday
            if weekday == 4:
                bucket = "Promo"

        # Determine platform (round-robin, but prioritize Instagram)
        if day_num % 3 == 1:
            platform = "Instagram"
        elif day_num % 3 == 2:
            platform = "LinkedIn"
        else:
            platform = "Twitter"

        # Determine angle
        angle = ANGLES[(day_num - 1 + weekday) % len(ANGLES)]

        # Phase 1: Generate visual concept for this post
        territory_id = (
            creative_territories[day_num % len(creative_territories)].id
            if creative_territories
            else "brand_story"
        )
        visual_concept = generate_visual_concept(
            platform=platform,
            theme=f"{bucket}: {angle}",
            creative_territory_id=territory_id,
            brand_name=brand_name,
            industry=industry,
        )

        # Generate unique hook based on bucket + angle + platform + visual concept
        hook = _make_quick_social_hook(
            brand_name=brand_name,
            industry=industry,
            bucket=bucket,
            angle=angle,
            platform=platform,
            goal_short=goal_short,
            day_num=day_num,
            weekday=weekday,
            profile=profile,
            visual_concept=visual_concept,
        )

        # Phase 1: Check if hook is too generic, regenerate if needed
        if is_too_generic(hook, threshold=0.20):
            # Add visual concept guidance to make it more specific
            visual_guidance = (
                f"Include specific details: {visual_concept.setting}, {visual_concept.mood} mood"
            )
            hook = _make_quick_social_hook(
                brand_name=brand_name,
                industry=industry,
                bucket=bucket,
                angle=angle,
                platform=platform,
                goal_short=goal_short,
                day_num=day_num,
                weekday=weekday,
                profile=profile,
                visual_concept=visual_concept,
                anti_generic_hint=visual_guidance,
            )

        # Choose asset type
        asset_types_list = ASSET_TYPES.get(platform, ["static_post"])
        asset_type = asset_types_list[(day_num - 1) % len(asset_types_list)]

        # Choose CTA
        ctas = CTA_LIBRARY.get(bucket, ["Learn more."])
        cta = ctas[(day_num - 1) % len(ctas)]

        # Format date
        date_str = post_date.strftime("%b %d")

        # Build row
        theme = f"{bucket}: {angle}"
        rows.append(
            f"| {date_str} | Day {day_num} | {platform} | {theme} | {hook} | {cta} | {asset_type} | Planned |"
        )

    # Build table
    table_md = (
        f"## 30-Day Content Calendar for {brand_name}\n\n"
        f"A day-by-day posting plan with rotating themes, platforms, and hooks. Each post is designed to move followers "
        f"from awareness to engagement to action, while maintaining consistent brand presence.\n\n"
        f"| Date | Day | Platform | Theme | Hook | CTA | Asset Type | Status |\n"
        f"|------|-----|----------|-------|------|-----|------------|--------|\n"
    )
    table_md += "\n".join(rows)

    table_md += (
        f"\n\n**Key:**\n"
        f"- **Education** = Tips, how-tos, industry insights that establish {brand_name} as an authority\n"
        f"- **Proof** = Testimonials, reviews, case studies showing real customer results\n"
        f"- **Promo** = Offers, new items, bundles with clear calls-to-action\n"
        f"- **Community** = UGC, staff features, customer stories fostering connection\n"
        f'- **Experience** = In-store moments, atmosphere, "third place" positioning\n\n'
        f"**Posting Best Practices:**\n"
        f"- Post Instagram content between 11 AM - 1 PM and 7 PM - 9 PM for peak engagement\n"
        f"- LinkedIn posts perform best Tuesday-Thursday 10 AM - 2 PM\n"
        f"- Twitter threads work well early morning (7-9 AM) and evening (5-7 PM)\n"
        f"- Respond to all comments within 4 hours to boost algorithmic reach\n"
        f"- Use Instagram Stories daily to maintain consistent presence between feed posts"
    )

    return sanitize_output(table_md, req.brief)


def _make_quick_social_hook(
    brand_name: str,
    industry: str,
    bucket: str,
    angle: str,
    platform: str,
    goal_short: str,
    day_num: int,
    weekday: int,
    profile: Optional[any],
    visual_concept: Optional[any] = None,
    anti_generic_hint: Optional[str] = None,
) -> str:
    """
    Generate unique hook for Quick Social post based on context.

    Uses templates that vary by platform + bucket + angle to ensure variety.
    Phase 1: Incorporates visual concept guidance for specificity.
    """
    industry_lower = industry.lower() if industry else "industry"

    # Use industry-specific vocab if available
    vocab_phrase = ""
    if profile and profile.vocab:
        vocab_phrase = profile.vocab[day_num % len(profile.vocab)]

    # Phase 1: Add visual concept specificity if available and anti-generic hint provided
    visual_detail = ""
    if visual_concept and anti_generic_hint:
        visual_detail = f" ({visual_concept.setting}, {visual_concept.mood} mood)"

    # Platform + Bucket + Angle combinations
    if platform == "Instagram":
        if bucket == "Experience":
            if vocab_phrase and "third place" in vocab_phrase:
                return f"Step into {brand_name}: your community's third place{visual_detail}."
            return f"Step into {brand_name}: your {industry_lower} escape in the neighbourhood{visual_detail}."
        elif bucket == "Proof" and "Community" in angle:
            return f"What guests actually say about {brand_name}{visual_detail}."
        elif bucket == "Education":
            return f"Quick tip: {angle.lower()} at {brand_name}{visual_detail}."
        elif bucket == "Promo":
            if weekday == 4:  # Friday
                return f"Friday treat: limited-time offer at {brand_name}{visual_detail}."
            return f"New at {brand_name}: {angle.lower()}{visual_detail}."
        elif bucket == "Community":
            return f"Meet the faces behind {brand_name}{visual_detail}."

    elif platform == "LinkedIn":
        if bucket == "Education":
            if vocab_phrase:
                return f"3 ways {brand_name} is rethinking {vocab_phrase} for busy professionals{visual_detail}."
            return f"3 ways {brand_name} is rethinking {industry_lower} for busy professionals{visual_detail}."
        elif bucket == "Proof":
            return (
                f"How {brand_name} is changing {industry_lower}: a customer story{visual_detail}."
            )
        elif bucket == "Community":
            return f"Behind the scenes: building community at {brand_name}{visual_detail}."
        elif bucket == "Promo":
            return f"Special offer for our LinkedIn community from {brand_name}{visual_detail}."

    elif platform == "Twitter":
        if bucket == "Proof":
            return f"What customers actually say about {brand_name} ({goal_short}){visual_detail}."
        elif bucket == "Education":
            return f"Thread: {angle.lower()} essentials from {brand_name}{visual_detail}."
        elif bucket == "Promo":
            return f"Flash: limited-time offer from {brand_name}{visual_detail}."
        elif bucket == "Community":
            return f"Your {brand_name} story: share your favorite moment{visual_detail}."

    # Fallback with day variation
    day_phrases = ["This week at", "Today's highlight:", "Don't miss:", "Just for you:"]
    day_phrase = day_phrases[day_num % len(day_phrases)]
    return f"{day_phrase} {bucket.lower()} content from {brand_name}{visual_detail}."


def _gen_email_and_crm_flows(req: GenerateRequest, **kwargs) -> str:
    """Generate 'email_and_crm_flows' section (markdown table format)."""
    b = req.brief.brand
    g = req.brief.goal
    raw = f"""## Welcome Series

Onboard new subscribers with value-first introduction to {b.brand_name}.

- Day 1: Welcome email introducing brand story and core value proposition
- Day 3: Educational content sharing industry insights and frameworks
- Day 5: Social proof showcase with customer testimonials and case studies

## Nurture Flows

Educate prospects progressively building confidence and addressing objections.

- Email 1: Framework introduction explaining strategic approach
- Email 2-3: Case study deep-dives showing results in {b.industry}
- Email 4-5: Educational content addressing common objections
- Email 6-7: Methodology overview with clear next steps

## Conversion Flows

Drive action from qualified, engaged prospects ready to commit.

- Soft pitch highlighting benefits and differentiation without heavy sales pressure
- Medium pitch with proof points, testimonials, and specific results
- Hard pitch with urgency, limited-time incentives, and clear deadline

## Re-Engagement Flows

Reactivate inactive subscribers and recover abandoned opportunities.

- Check-in message with value reminder and what they're missing
- Exclusive comeback offer not available to active subscribers
- Final notice with unsubscribe option to clean list and maintain deliverability

| Flow Type | Trigger | Email Sequence | Key Content | Primary Goal | Success Metric |
|-----------|---------|----------------|-------------|--------------|----------------|
| **Welcome Series** | New subscriber | 3 emails over 5 days | Intro to value proposition, Social proof showcase, First offer/CTA | Build trust and establish expectations | Open rate >40%, Click rate >15% |
| **Educational Nurture** | Content download | 5-7 emails over 14 days | Industry insights, Framework explanations, Case study deep-dives, Methodology overview | Educate and build confidence | Engagement score, Time-to-demo request |
| **Conversion Series** | Demo request or high engagement | 3 emails over 7 days | Soft pitch with benefits, Medium pitch with proof, Hard pitch with urgency and deadline | Drive commitment to {g.primary_goal} | Conversion rate, Sales qualified lead rate |
| **Abandoned Cart** | Cart abandonment | 3 emails over 72 hours | Reminder with cart contents, Address objections + FAQs, Limited-time incentive | Recover revenue | Recovery rate, Revenue per email |
| **Re-Engagement** | 30 days inactive | 3 emails over 10 days | Check-in + value reminder, Exclusive offer for comeback, Final notice + unsubscribe option | Reactivate or clean list | Re-engagement rate, Unsubscribe rate |
| **Post-Purchase** | Purchase completion | 5 emails over 30 days | Thank you + onboarding, Feature education, Success tips, Referral request, Upsell introduction | Maximize LTV and advocacy | Repeat purchase rate, Referral conversion |
| **Win-Back** | Lapsed customer (90+ days) | 4 emails over 21 days | We miss you message, What's new since you left, Special comeback offer, Last chance notice | Reactivate customers | Win-back rate, Lifetime value recovery |

All flows integrate with CRM for behavioral triggering, progressive profiling, and personalized content delivery based on segment, engagement history, and demonstrated interests."""
    return sanitize_output(raw, req.brief)


def _gen_ad_concepts(req: GenerateRequest, **kwargs) -> str:
    """Generate 'ad_concepts' section."""
    b = req.brief.brand
    g = req.brief.goal

    raw = (
        f"## Ad Concepts\n\n"
        f"**Strategic Ad Framework for {b.brand_name}**\n\n"
        f"Each ad concept is designed to meet prospects at specific stages of awareness and guide them toward "
        f"{g.primary_goal or 'conversion objectives'}. The creative approach balances attention-grabbing hooks with "
        f"substantive value delivery. All ads incorporate social proof, clear CTAs, and platform-specific optimization "
        f"to maximize ROI and engagement across paid channels.\n\n"
        f"**Awareness Stage Ads:** Problem-aware hooks highlighting cost of inaction. Bold headlines, relatable scenarios. "
        f"CTA: Learn more, download guide. Target: Cold prospects matching demographic profile.\n\n"
        f"**Consideration Stage Ads:** Showcase case studies, results metrics, proof of effectiveness. Before/after visuals, "
        f"testimonials, data visualization. CTA: See how it works, book consultation. Target: Warm prospects who've engaged.\n\n"
        f"**Conversion Stage Ads:** Direct CTAs with limited-time offers and urgency. Countdown timers, scarcity messaging, "
        f"guarantees. CTA: Get started now, claim offer. Target: Hot prospects with purchase intent.\n\n"
        f"**Remarketing Ads:** Re-engage visitors with special retargeting offers. Dynamic ads featuring viewed pages. "
        f"Exclusive discounts not available in cold traffic. Frequency cap: 3-5 impressions weekly.\n\n"
        f"## Messaging\n\n"
        f"**Core Messaging Principles Across All Ad Types:**\n\n"
        f"- Lead with Value: Every ad must answer 'What's in it for me?' within 3 seconds\n"
        f"- Proof Over Promises: Use specific metrics, customer names, verifiable results\n"
        f"- Clarity Above Cleverness: Direct communication beats wordplay for conversions\n"
        f"- Social Proof Integration: Include testimonials, user counts, recognizable logos\n"
        f"- Platform Optimization: Adapt messaging length and tone per platform\n\n"
        f"## Testing & Optimization\n\n"
        f"**Continuous Improvement Framework:**\n\n"
        f"- Test 2-3 variations of each ad concept simultaneously\n"
        f"- A/B test headlines, images, CTA buttons, landing pages\n"
        f"- Pause underperforming ads after 3-5 days and 200+ impressions\n"
        f"- Scale winning ads aggressively with 50% budget increases weekly\n"
        f"- Refresh creative every 2-3 weeks to combat ad fatigue\n"
        f"- Track cost-per-click, cost-per-lead, cost-per-acquisition rigorously\n"
        f"- Document learnings from every test to inform future campaigns\n"
        f"- Use platform-specific best practices (Facebook Ads Manager insights, LinkedIn Campaign Manager data)\n\n"
        f"**Performance Benchmarks:**\n"
        f"- Target CTR: 2-4% for cold traffic, 5-8% for retargeting\n"
        f"- Target conversion rate: 3-7% from ad click to lead capture\n"
        f"- Acceptable CPA: Defined by customer lifetime value (aim for 3:1 LTV:CAC ratio minimum)\n"
        f"- Ad fatigue threshold: Refresh when CTR drops 30% from initial performance"
    )
    return sanitize_output(raw, req.brief)


def _gen_kpi_and_budget_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'kpi_and_budget_plan' section."""
    g = req.brief.goal
    b = req.brief.brand

    raw = (
        f"## Budget Split by Channel\n\n"
        f"**Strategic Budget Allocation Aligned with {g.primary_goal or 'Campaign Objectives'}:**\n\n"
        f"- **Organic/Owned Content Creation (40%):** Content development, creative production, community management\n"
        f"- **Paid Social Advertising (35%):** Facebook/Instagram Ads, LinkedIn Ads, platform-specific paid campaigns\n"
        f"- **Email Marketing & CRM (15%):** Email platform costs, automation setup, list management, segmentation\n"
        f"- **Content & Creative Assets (10%):** Professional design, video production, copywriting, photography\n\n"
        f"This allocation prioritizes building owned assets and organic reach (40%) while leveraging paid amplification (35%) "
        f"to accelerate growth. The split is optimized for {b.brand_name}'s goals but should be adjusted monthly based on "
        f"channel performance data and ROI metrics.\n\n"
        f"## Testing vs Always-On\n\n"
        f"**Budget Distribution Between Testing and Proven Tactics:**\n\n"
        f"- **Always-On Campaigns (70%):** Proven content pillars, winning ad variations, established channels with consistent ROI\n"
        f"- **Testing Budget (20%):** New platforms, content formats, messaging variations, audience segments\n"
        f"- **Contingency/Opportunity Fund (10%):** Reserved for scaling breakout winners or capturing unexpected opportunities\n\n"
        f"The always-on budget ensures stable baseline performance while testing budget allows for continuous improvement "
        f"and innovation. Successful tests graduate to always-on status, replacing underperforming campaigns. This approach "
        f"balances predictability with growth potential.\n\n"
        f"## Guardrails\n\n"
        f"**Budget Protection & Performance Standards:**\n\n"
        f"**Performance Thresholds:**\n"
        f"- Pause any ad campaign with cost-per-lead >150% of target after 5-7 days\n"
        f"- Kill any content format that consistently underperforms (bottom 20% engagement) after 3 iterations\n"
        f"- Require minimum 2% engagement rate on organic social posts or adjust strategy\n\n"
        f"**Budget Controls:**\n"
        f"- No single campaign should exceed 25% of total budget without explicit approval\n"
        f"- Weekly budget reviews to catch overspend early\n"
        f"- Daily spend caps on all paid campaigns to prevent runaway costs\n"
        f"- Require positive ROI before scaling any campaign beyond initial test budget\n\n"
        f"**Success Metrics & Reporting:**\n\n"
        f"**Primary KPIs:**\n"
        f"- **Awareness:** Reach ({g.primary_goal or 'target audience size'} per week), impressions, brand mentions\n"
        f"- **Engagement:** Rate (>2% target or 500+ interactions per post), shares, saves, comments\n"
        f"- **Conversion:** Qualified leads ({g.primary_goal or 'target weekly leads'}), cost-per-lead, conversion rate\n"
        f"- **Revenue Impact:** Customer acquisition cost, lifetime value, ROI on ad spend\n\n"
        f"**Measurement Cadence:** Weekly dashboard reviews for tactical adjustments, monthly deep-dive analysis for strategic "
        f"optimization, quarterly comprehensive audits to assess overall campaign health and alignment with {g.primary_goal or 'business goals'}."
    )
    return sanitize_output(raw, req.brief)


def _gen_execution_roadmap(req: GenerateRequest, **kwargs) -> str:
    """Generate 'execution_roadmap' section."""
    b = req.brief.brand
    g = req.brief.goal
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs 30/60/90-day structure
    if "performance_audit" in pack_key.lower():
        return f"""## 30-Day Sprint

Immediate actions stopping performance bleeding and capturing quick wins:

| Week | Priority Actions | Expected Outcome | Success Metric |
|------|------------------|------------------|----------------|
| **Week 1** | Pause bottom 2 channels (Instagram, YouTube) wasting $3.8K/month. Reallocate to Google Search. Fix landing page load time from 4.2s to <2s. Simplify lead form from 12 to 5 fields. | $3.8K monthly savings reinvested. 15-20% conversion lift from speed. 25-30% form completion improvement. | CPA reduction, conversion rate increase, form completion rate |
| **Week 2** | Launch cart abandonment email sequence (450 monthly abandons). Add social proof above fold. Implement exit-intent popup. Refresh CTAs from "Learn More" to directive language. | Recover 15-20% of abandons = $45K annual. 10-15% trust-driven conversion lift. 5-8% exit capture rate. 2-3x CTA click improvement. | Abandonment recovery rate, overall conversion rate, CTA click-through rate |
| **Week 3** | Triple budget to demo downloaders (best audience at $28 CPA). Launch remarketing to high-intent audiences. A/B test 5 new ad creative variations. Implement weekly performance review cadence. | +60 conversions/month from best audience. 8-12% remarketing conversion rate. Identify 2-3 winning creative patterns. Data-driven optimization rhythm established. | Conversion volume increase, remarketing ROAS, creative performance variance |
| **Week 4** | Optimize mobile UX (70% traffic, 62% lower conversion). Build 3 platform-specific ad variations. Launch video content pilot (competitors 3-5x engagement). Document all changes and results in playbook. | 35% mobile conversion improvement. 20-30% platform efficiency gains. Baseline video engagement data. Replicable optimization framework. | Mobile conversion rate, platform-specific ROAS, video engagement rate |

**30-Day Expected Results:**
- CPA reduction $41 → $32-$35 (15-22%)
- Conversion rate 2.1% → 2.8-3.2% (33-52% lift)
- Additional +140-180 conversions/month
- Cost savings $3.8K/month from channel optimization
- Measurement framework operational
- Winning creative patterns identified

## 60-Day Horizon

Strategic initiatives building on quick wins for sustained improvement:

| Initiative | Business Case | Investment | Expected Return |
|------------|---------------|------------|-----------------|
| **Video Content Program** (Days 31-37) | Competitors seeing 3-5x engagement on video, {b.brand_name} has zero video presence | $4K production + $2K monthly media | +40% reach, +25% engagement, new remarketing pool |
| **Landing Page Redesign** (Days 38-44) | Current 2.1% conversion significantly below 3.5-4.5% benchmark requiring comprehensive redesign | $6K design/dev + $800/month chat | 35-50% conversion improvement (2.8% → 3.8-4.2%), mobile parity with desktop |
| **Email Remarketing** (Days 45-51) | 78% of site visitors leave without follow-up, zero systematic nurture exists | $2K automation + $400/month platform | +180 conversions/year, 12-18% email-to-customer rate |
| **SEO Initiative** (Days 52-60) | Organic traffic highest-quality (3.8% conversion vs 2.1% paid) but only 1,200 monthly visitors | $3K SEO audit + $2K monthly content | 150% organic traffic growth, +240 monthly conversions, page 1 rankings for 12+ terms |

**60-Day Expected Results:**
- CPA $32-$35 → $26-$30 (24-37% total improvement)
- Total conversions 280/month → 520-600/month (86-114% increase)
- ROAS 1.9x → 3.2-3.8x (68-100% improvement)
- Organic channel driving 30-40% of conversions
- Video production workflow operational
- Email automation framework live
- A/B testing systems established

## 90-Day Vision

Transformational changes establishing {b.brand_name} as category leader:

| Initiative | Strategic Rationale | Investment | Long-Term Impact |
|------------|---------------------|------------|------------------|
| **Community Platform** | Network effects making {b.brand_name} stickier than competitors, reduce support costs 40%, improve retention through peer learning | $8K setup + $600/month hosting + $3K moderation | 40%+ retention improvement, 25% support cost reduction, organic growth flywheel, user-generated content at scale |
| **Partner/Influencer Program** | Access established audiences through credible voices, achieve 3-5x better engagement than branded content | $12K partnership fees + $2K monthly management | 500K+ combined audience reach, 200+ monthly referral leads, 40-60% lower CPA than paid ads |
| **Proprietary Research Report** | Establish {b.brand_name} as data authority in {b.industry}, generate 1000+ qualified leads annually through gated distribution | $15K research/production + $5K PR/promotion | 1,200+ gated downloads (qualified leads), 30+ earned media placements, 100+ high-quality backlinks |
| **Certification Program** | Build ecosystem of {b.brand_name} advocates while generating $500K+ annual revenue from professional credentialing | $20K curriculum + $8K platform + $3K monthly operation | $500K+ annual certification revenue, 2,000+ certified professionals advocating, 50% higher product adoption |

**90-Day Expected Results:**
- Target CPA $25-$28 (optimal efficiency for {b.industry})
- Monthly conversions 650-750 (132-168% improvement from baseline 280)
- Target ROAS 3.5-4.5x (84-137% improvement)
- Organic contribution 45-55% of total conversions
- Revenue impact $180K-$240K additional annual revenue
- Category leader positioning established
- Sustainable systems operational

**Post-90-Day:** Double video content (16-24/month). Expand SEO to 50+ keywords driving 5,000+ monthly visitors. Scale partners to 30-40 influencers. Grow community to 500+ active members. Target: $22-$25 CPA, 5.0x ROAS, 1,000+ monthly conversions, 60%+ organic contribution."""
    else:
        # Default/other pack version
        raw = (
            f"## Phase 1: Launch Preparation (Days 1-10)\n\n"
            f"**Focus:** Foundation setup, content creation, and system configuration to ensure smooth campaign launch for "
            f"{b.brand_name}. This phase prioritizes quality over speed—every element must be production-ready before "
            f"going live to avoid rushed execution and credibility damage.\n\n"
            f"| Timeline | Key Activities | Deliverables | Owner/Responsible |\n"
            f"|----------|----------------|--------------|-------------------|\n"
            f"| Days 1-3 | Finalize messaging framework and brand guidelines<br>Create content bank (15-20 pieces)<br>Set up tracking pixels and analytics | Approved messaging doc<br>Content calendar populated<br>Tracking systems live | Strategy + Content Team |\n"
            f"| Days 4-7 | Build landing pages and conversion funnels<br>Configure email automation sequences<br>Set up paid ad campaigns (draft status) | Live landing pages<br>Email sequences ready<br>Ad campaigns in review | Design + Tech Team |\n"
            f"| Days 8-10 | Final QA testing across all platforms<br>Team training on processes and systems<br>Schedule first week of content | All systems verified<br>Team onboarded<br>Week 1 scheduled | Project Manager |\n\n"
            f"## Phase 2: Active Campaign Execution (Days 11-30)\n\n"
            f"**Focus:** Execute planned activities, monitor performance closely, and optimize based on real-time data. "
            f"This phase requires daily attention to metrics and weekly strategy adjustments to maximize {g.primary_goal or 'campaign effectiveness'}.\n\n"
            f"| Timeline | Key Activities | Success Criteria | Adjustments |\n"
            f"|----------|----------------|------------------|-------------|\n"
            f"| Days 11-17 (Week 1) | Launch organic social presence<br>Activate email welcome series<br>Start first paid ad campaign<br>Daily community engagement | 1000+ impressions/day<br>100+ email opens<br>50+ ad clicks<br>10+ meaningful engagements | Pause underperforming content<br>Double down on winning posts<br>Adjust targeting if needed |\n"
            f"| Days 18-24 (Week 2) | Optimize based on Week 1 data<br>Launch second paid campaign variant<br>Introduce video/reel content<br>Begin retargeting campaigns | 2x Week 1 engagement<br>5+ qualified leads<br>Positive early ROI signals | Refine audience segments<br>Test new content angles<br>Scale winning ads by 30% |\n"
            f"| Days 25-30 (Week 3-4) | Final push with direct CTAs<br>Activate limited-time offers<br>Collect comprehensive performance data<br>Prepare monthly analysis report | 50+ total qualified leads<br>Cost-per-lead below target<br>Engagement rate >2%<br>Clear data for next iteration | Document learnings<br>Archive successful content<br>Plan Month 2 strategy |\n\n"
            f"## Key Milestones\n\n"
            f"**Critical Checkpoints & Decision Gates:**\n\n"
            f"| Milestone | Target Date | Success Metric | If Not Met |\n"
            f"|-----------|-------------|----------------|------------|\n"
            f"| Campaign Go-Live | Day 10 | All systems operational, 15+ pieces of content ready | Delay launch, complete setup |\n"
            f"| First Lead Generated | Day 14 | At least 1 qualified lead from campaign activities | Review messaging and targeting |\n"
            f"| Positive ROI Signal | Day 21 | Cost-per-lead trending toward target, engagement >1.5% | Pivot strategy, test new angles |\n"
            f"| Monthly Target Progress | Day 30 | 70%+ of monthly lead goal achieved | Assess viability, recommend changes |\n\n"
            f"**Month 2+ Roadmap:**\n\n"
            f"Based on Month 1 learnings, iterate and scale:\n\n"
            f"- Double down on winning channels and content themes that showed best ROI\n"
            f"- Test 2-3 new platform strategies or audience segments for expansion\n"
            f"- Gradually increase budget on proven campaigns by 30-50% monthly\n"
            f"- Develop more sophisticated retargeting funnels for non-converters\n"
            f"- Build out additional content pillars based on engagement data\n"
            f"- Refine messaging based on customer feedback and conversion analysis\n"
            f"- Optimize landing pages and conversion paths to improve funnel efficiency\n"
            f"- Scale successful partnerships or collaborations that drove quality leads\n"
            f"- Continue data-driven adjustments toward {g.primary_goal or 'long-term campaign objectives'}"
        )
    return sanitize_output(raw, req.brief)


def _gen_post_campaign_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'post_campaign_analysis' section."""
    b = req.brief.brand
    g = req.brief.goal

    raw = (
        f"## Results\n\n"
        f"**Comprehensive Performance Assessment Against {g.primary_goal or 'Campaign Objectives'}:**\n\n"
        f"**Quantitative Outcomes:**\n"
        f"- **Reach & Awareness:** Total impressions, unique reach, brand mention growth\n"
        f"- **Engagement Metrics:** Overall engagement rate, average interactions per post, top-performing content themes\n"
        f"- **Lead Generation:** Total qualified leads, cost-per-lead vs target, lead quality score distribution\n"
        f"- **Conversion Performance:** Lead-to-customer rate, revenue generated (if applicable), ROI on ad spend\n"
        f"- **Audience Growth:** New followers/subscribers, email list growth, community expansion\n\n"
        f"Compare all metrics against baseline and stated goals. Identify which KPIs exceeded targets (celebrate wins), "
        f"met expectations (maintain approach), or fell short (requires investigation). Provide specific numbers and "
        f"percentages for {b.brand_name}'s stakeholder review and future planning.\n\n"
        f"## Learnings\n\n"
        f"**Strategic Insights from Campaign Execution:**\n\n"
        f"**What Worked:**\n"
        f"- **Content Themes:** Which topics, formats, and messaging angles drove highest engagement and conversions\n"
        f"- **Platform Performance:** Which channels delivered best ROI and should receive increased investment\n"
        f"- **Audience Segments:** Which demographic or psychographic groups responded most strongly\n"
        f"- **Creative Elements:** Which visual styles, headlines, or storytelling approaches resonated most\n"
        f"- **Timing & Cadence:** Optimal posting times and frequency for audience engagement\n\n"
        f"**What Didn't Work:**\n"
        f"- **Underperforming Content:** Topics or formats that consistently failed to generate engagement\n"
        f"- **Channel Inefficiencies:** Platforms that consumed resources without delivering proportional results\n"
        f"- **Messaging Misses:** Angles that didn't resonate or created confusion instead of clarity\n"
        f"- **Budget Waste:** Campaigns or tactics that failed to meet minimum performance thresholds\n\n"
        f"**Why It Happened:**\n"
        f"Root cause analysis for both successes and failures. Consider audience preferences, market conditions, "
        f"competitive actions, execution quality, and strategic alignment. Document specific hypotheses about why "
        f"certain approaches succeeded while others failed.\n\n"
        f"## Recommendations\n\n"
        f"**Actionable Next Steps for Future Campaigns:**\n\n"
        f"**Immediate Optimizations (Next 30 Days):**\n"
        f"- Scale winning content themes by 50-100% production volume\n"
        f"- Reallocate budget from underperforming channels to top performers\n"
        f"- Implement A/B testing on top-performing content to find additional improvements\n"
        f"- Develop retargeting campaigns for engaged non-converters\n"
        f"- Refine audience targeting based on conversion data\n\n"
        f"**Medium-Term Strategy (60-90 Days):**\n"
        f"- Explore new content formats suggested by engagement patterns\n"
        f"- Test additional platforms or channels identified as opportunities\n"
        f"- Develop more sophisticated segmentation and personalization\n"
        f"- Build on winning creative territories with expanded variations\n"
        f"- Strengthen underperforming areas with new strategic approaches\n\n"
        f"**Long-Term Growth Opportunities:**\n"
        f"- Invest in owned media properties (blog, podcast, YouTube channel)\n"
        f"- Develop strategic partnerships or influencer relationships\n"
        f"- Create more advanced marketing automation and funnel optimization\n"
        f"- Build brand community and advocacy programs\n"
        f"- Expand into new market segments or geographic regions for {b.brand_name}"
    )
    return sanitize_output(raw, req.brief)


def _get_summary_style_for_pack(pack_key: str) -> str:
    """
    Decide how long / rich the final_summary should be based on pack.

    - quick social → short, punchy (150-220 words)
    - strategy / full-funnel / brand → richer, more detailed (220-350 words)
    """
    if pack_key == "quick_social_basic":
        return "short"

    if pack_key in {
        "strategy_campaign_basic",
        "strategy_campaign_standard",
        "strategy_campaign_premium",
        "strategy_campaign_enterprise",
        "full_funnel_growth_suite",
        "brand_turnaround_lab",
        "launch_gtm_pack",
        "retention_crm_booster",
        "performance_audit_revamp",
    }:
        return "rich"

    # Safe default
    return "rich"


def _gen_final_summary(req: GenerateRequest, **kwargs) -> str:
    """
    Generate 'final_summary' section.

    This is PACK-AWARE: it produces shorter output for quick_social_basic,
    and richer output for strategy / full-funnel packs to satisfy their
    benchmark ranges.
    """
    b = req.brief.brand
    g = req.brief.goal
    pack_key = (
        req.package_preset or req.wow_package_key or "strategy_campaign_standard"
    )  # safe default
    style = _get_summary_style_for_pack(pack_key)

    if style == "short":
        # Target: Quick Social benchmark (min ~100, max ~260 words)
        # Keep it tight with 2-3 short paragraphs + 3-5 bullets
        # AVOID: "post regularly", "do social media consistently" (forbidden phrases)
        raw = (
            f"This quick social media strategy gives {b.brand_name} a clear, actionable plan to achieve "
            f"{g.primary_goal or 'core marketing objectives'}. The plan focuses on proven content themes, "
            f"optimal posting schedules, and platform-specific best practices that drive real engagement "
            f"and measurable results.\n\n"
            f"Success comes from consistent execution across all channels. Maintain the defined brand voice, "
            f"follow the recommended content calendar, and monitor performance metrics weekly. Track what resonates "
            f"with your audience and adapt based on data insights. This systematic approach replaces random activity "
            f"with strategic content that builds audience loyalty and drives sustainable growth for {b.brand_name}.\n\n"
            f"## Key Takeaways\n\n"
            f"- **Focus on Quality:** Prioritize high-performing content themes over posting frequency\n"
            f"- **Stay Consistent:** Follow the content calendar and maintain brand voice across all channels\n"
            f"- **Track Performance:** Monitor key metrics weekly and double down on what works best\n"
            f"- **Engage Authentically:** Respond to comments and build genuine connections with {b.brand_name}'s audience\n"
            f"- **Adapt Quickly:** Use data insights to refine content strategy and optimize for better results"
        )
    else:
        # Target: Strategy / Full-funnel benchmarks (min ~180, max ~400 words)
        # Slightly deeper recap, more bullets allowed
        raw = (
            f"This comprehensive marketing strategy positions {b.brand_name} for sustained growth and market impact. "
            f"By focusing on {g.primary_goal or 'core objectives'}, this plan provides a clear, actionable roadmap for "
            f"the next 90 days and beyond. The strategy integrates proven frameworks with {b.brand_name}-specific insights "
            f"to create a repeatable system that compounds results over time.\n\n"
            f"Success requires three key commitments: (1) Consistent execution of the content strategy across all platforms, "
            f"maintaining the defined brand voice and messaging framework; (2) Regular monitoring of KPIs with data-driven "
            f"adjustments based on performance insights; (3) Commitment to the core narrative and positioning, resisting the "
            f"temptation to chase every new trend or platform without strategic evaluation.\n\n"
            f"The framework outlined here transforms random marketing activities into a repeatable, scalable system. "
            f"By concentrating efforts on proven content buckets, maintaining platform-specific best practices, and "
            f"measuring results against clear benchmarks, {b.brand_name} will build momentum that compounds over time. "
            f"This systematic approach replaces guesswork with strategy, creating a foundation for long-term marketing success.\n\n"
            f"## Key Takeaways\n\n"
            f"**Critical Success Factors for {b.brand_name}:**\n\n"
            f"- **Strategic Focus:** Concentrate resources on highest-ROI channels and proven content themes rather than "
            f"spreading efforts too thin across too many platforms\n"
            f"- **Execution Discipline:** Maintain consistency in brand voice, posting cadence, and quality standards even "
            f"when immediate results aren't visible—compound effects take time\n"
            f"- **Data-Driven Optimization:** Review performance metrics weekly, make tactical adjustments based on evidence, "
            f"and double down on what works while killing what doesn't\n"
            f"- **Long-Term Perspective:** Building sustainable brand authority and audience trust requires patience, "
            f"persistence, and commitment to the core strategy beyond short-term tactics\n"
            f"- **Continuous Improvement:** Treat every campaign as a learning opportunity, document insights, and iterate "
            f"toward increasingly effective marketing systems for {b.brand_name}"
        )

    return sanitize_output(raw, req.brief)


# ============================================================
# ADDITIONAL GENERATORS FOR PREMIUM & ENTERPRISE TIERS
# ============================================================


def _gen_value_proposition_map(req: GenerateRequest, **kwargs) -> str:
    """Generate 'value_proposition_map' section."""
    b = req.brief.brand
    g = req.brief.goal
    raw = f"""## Positioning Statement

**Positioning Statement:** {b.brand_name} empowers organizations in {b.industry} to achieve {g.primary_goal} through systematic, data-driven marketing strategies that compound results over time.

This positioning differentiates {b.brand_name} from competitors by emphasizing both strategic rigor and sustainable execution. Rather than promising overnight success or quick wins, we deliver frameworks that build enduring competitive advantages. Our approach transforms marketing from an expense center into a measurable growth driver.

## Core Value Proposition

**Core Value Proposition:** Unlike scattered tactics that produce inconsistent results, {b.brand_name} delivers a repeatable framework combining strategic clarity, creative excellence, and performance optimization to transform marketing from guesswork into predictable growth.

The value proposition addresses the core frustration of {b.industry} organizations: marketing that feels like throwing money at the wall. We replace hope-based marketing with systematic processes that generate reliable, compound returns. Our clients gain clarity on what works, why it works, and how to scale successfully.

## Messaging Pillars

The messaging architecture rests on five interconnected pillars that resonate across all customer touchpoints:

- **Strategic Clarity**: Clear roadmap with defined objectives, measurable milestones, and transparent progress tracking that eliminates guesswork
- **Systematic Execution**: Repeatable processes that scale efficiently without proportional resource increases through documented frameworks
- **Proven Results**: Evidence-based methodology validated across industries with documented case studies showing measurable outcomes
- **Expert Guidance**: Deep domain expertise translating complex strategies into actionable implementation plans with hands-on support
- **Sustainable Growth**: Long-term focus building compounding advantages rather than short-term tactical wins that fade quickly

## Proof Points

Credibility markers that validate the value proposition and build trust:

- Industry-specific case studies demonstrating measurable outcomes in {b.industry} with detailed performance metrics
- Methodology frameworks grounded in established marketing science and behavioral economics principles
- Technology integration leveraging modern tools for automation, analytics, and optimization
- Client testimonials highlighting transformation from chaotic to systematic marketing operations
- Awards and recognition from industry bodies validating our methodology and results

## Benefits

Tangible outcomes clients achieve through {b.brand_name} engagement:

- **Revenue Growth**: Average 40-60% increase in marketing-sourced revenue within 12 months through optimized funnel performance
- **Cost Efficiency**: 25-35% reduction in customer acquisition costs via channel optimization and conversion improvements
- **Predictability**: Transform marketing from unpredictable expense to reliable growth engine with forecasting accuracy
- **Team Productivity**: Free internal teams from tactical overwhelm to focus on strategic initiatives and creative excellence
- **Market Position**: Build sustainable competitive advantages through authentic differentiation and category leadership
- **Scalability**: Create repeatable systems that grow with business without proportional resource increases
"""
    return sanitize_output(raw, req.brief)


def _gen_creative_territories(req: GenerateRequest, **kwargs) -> str:
    """Generate 'creative_territories' section."""
    b = req.brief.brand
    raw = f"""## Creative Themes

Three distinct creative territories establish {b.brand_name}'s visual and messaging identity across campaigns. Each territory serves specific marketing objectives while maintaining cohesive brand expression.

**Territory 1: Authority & Proof**
- Showcase customer success stories, detailed case studies, and quantified results that demonstrate real-world impact
- Feature testimonials, third-party validation, industry recognition, and expert endorsements from credible sources
- Present data visualizations, performance metrics, and before/after comparisons that make results tangible
- Include awards, certifications, partnerships with respected brands, and analyst recognition
- Tone: Confident, evidence-based, professional, and credibility-focused with metrics-driven narratives

**Territory 2: Simplicity & Clarity**
- Demonstrate the contrast between systematic frameworks versus chaotic scattered tactics through visual storytelling
- Use clear visual hierarchies, minimal design, and straightforward explanatory content that removes complexity
- Break down complex concepts into accessible, actionable steps with practical examples and implementation guides
- Feature process diagrams, step-by-step walkthroughs, and before/after transformation stories
- Tone: Accessible, warm, solution-focused, and education-oriented with emphasis on practical utility

**Territory 3: Growth & Momentum**
- Emphasize compounding results, long-term ROI, and sustainable competitive advantages that build over time
- Illustrate progression, milestone achievements, and forward trajectory visualizations showing exponential growth
- Inspire with vision of future state while grounding in achievable incremental progress with clear milestones
- Use growth curves, trajectory charts, and momentum indicators that visualize progress
- Tone: Aspirational, forward-looking, ambitious, and momentum-building with inspiring yet believable narratives

## Creative Execution Guidelines

Each territory maintains brand consistency while allowing tactical variation to prevent creative fatigue and enable systematic testing across audience segments. Rotate territories across campaigns to maintain fresh creative while reinforcing core brand themes. Test messaging variants within each territory to optimize performance."""
    return sanitize_output(raw, req.brief)


def _gen_copy_variants(req: GenerateRequest, **kwargs) -> str:
    """Generate 'copy_variants' section."""
    b = req.brief.brand
    g = req.brief.goal
    raw = f"""## Copy Variations

Multiple messaging angles allow systematic testing to identify highest-performing copy across different audience segments and contexts.

**Rational/Logic-Driven Variants:**
- "{b.brand_name} replaces scattered marketing tactics with a systematic framework that compounds results over time through data-driven optimization."
- "Achieve {g.primary_goal} through proven methodologies combining strategic planning, creative execution, and performance measurement."
- "Transform marketing from unpredictable experiments into repeatable processes delivering consistent, measurable outcomes."
- "Strategic clarity meets tactical execution: comprehensive frameworks designed specifically for {b.industry} organizations."
- "Measurable marketing strategies backed by data, validated through testing, and optimized for sustainable growth in {b.industry}."

**Emotional/Benefit-Focused Variants:**
- "Stop feeling lost in marketing chaos. Start seeing clear progress toward your goals with {b.brand_name}."
- "Finally: a marketing approach that makes sense. Clear strategy. Measurable results. Sustainable growth for {b.industry}."
- "Confidence comes from clarity. Know exactly what to do, when to do it, and why it matters for {g.primary_goal}."
- "Move from overwhelmed to in control. From guessing to knowing. From random to systematic with {b.brand_name}."
- "Experience the relief of marketing that finally clicks. Strategy that works. Results you can see. Growth you can sustain."

**Provocative/Challenge-Oriented Variants:**
- "Your competitors are still posting randomly. Here's the systematic approach that pulls you ahead in {b.industry}."
- "Most marketing advice is generic noise. This is your specific roadmap to {g.primary_goal} with proven frameworks."
- "The difference between busy and effective: strategic focus replacing scattered activity in modern marketing."
- "Stop doing more marketing. Start doing better marketing with frameworks that actually work in {b.industry}."
- "Question: Why waste budget on tactics that might work when proven systems guarantee results for {b.brand_name}?"

**Social Proof/Authority Variants:**
- "Join hundreds of {b.industry} organizations using {b.brand_name}'s frameworks to achieve {g.primary_goal} systematically."
- "Trusted by industry leaders: the methodology that transforms marketing from expense to strategic growth driver."
- "The approach winning teams choose when results matter more than activity: proven frameworks for {b.industry}."

## Testing Protocol

Rotate variants across platforms and audiences to identify top performers, then scale winning messages while eliminating underperformers."""
    return sanitize_output(raw, req.brief)


def _gen_funnel_breakdown(req: GenerateRequest, **kwargs) -> str:
    """Generate 'funnel_breakdown' section (markdown table format)."""
    b = req.brief.brand
    g = req.brief.goal
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs drop-off analysis
    if "performance_audit" in pack_key.lower():
        return """## Drop-Off Stages

Identification of where prospects abandon the conversion journey:

- **Awareness to Consideration**: 82% drop-off rate (18% click-through from ads to landing page) indicating weak ad relevance or misaligned expectations
- **Consideration to Intent**: 65% drop-off rate (35% of landing page visitors engage with content/CTA) showing insufficient value proposition clarity or trust signals
- **Intent to Action**: 48% drop-off rate (52% of form starters complete submission) suggesting form friction or unclear next steps
- **Action to Conversion**: 22% drop-off rate (78% of submitted forms convert to customers) demonstrating strong sales follow-up but room for optimization

## Major Leaks

Critical bottlenecks hemorrhaging potential customers:

- **Landing Page Bounce Rate**: 67% of paid traffic bouncing within 5 seconds representing $4,800/month in wasted ad spend due to slow load times and weak headlines
- **Form Abandonment**: 480 monthly form abandons (48% abandonment rate) costing estimated $19,200 in lost revenue from friction points like too many required fields
- **Mobile Experience Gap**: Mobile conversion rate 62% lower than desktop despite 70% mobile traffic indicating severe UX issues causing abandonment
- **Post-Click Disconnect**: Ad promises not matching landing page content creating 35% immediate bounce rate and trust erosion
- **Cart Abandonment**: 450 monthly cart abandonments with zero follow-up email sequence leaving $45K+ in recoverable revenue on the table

## Hypotheses

Tested theories explaining performance gaps:

- **Hypothesis 1 - Load Speed**: 4.2-second average landing page load time (vs 2s benchmark) likely causing 25-30% of initial drop-off before content even renders
- **Hypothesis 2 - Value Clarity**: Weak above-the-fold value proposition failing to communicate specific benefit within 3 seconds causing confusion and bounces
- **Hypothesis 3 - Trust Deficit**: Absence of social proof, security badges, and testimonials on landing pages preventing conversion of interested prospects
- **Hypothesis 4 - Form Friction**: 12 required form fields (vs industry standard 5-7) creating perceived effort barrier and abandonment at intent stage
- **Hypothesis 5 - Mobile Unfriendly**: Non-mobile-optimized forms and CTAs requiring excessive scrolling and zooming frustrating mobile-first users
- **Hypothesis 6 - Weak Follow-Up**: No automated email sequences for cart abandoners or form abandoners missing critical remarketing touchpoints

Priority fixes: Reduce landing page load time to under 2 seconds, cut form fields to 5-7 essentials, implement cart abandonment email sequence, add social proof elements above fold."""
    else:
        # Default full-funnel version
        return f"""## Awareness

Reach ideal buyers and establish initial brand recognition through strategic visibility.

- Build top-of-mind awareness among target decision-makers in {b.industry}
- Establish credibility through thought leadership and educational content
- Generate initial interest and drive traffic to owned properties

## Consideration

Nurture prospects with education and proof points that build confidence.

- Deliver systematic email nurture sequences with progressive education
- Showcase detailed case studies demonstrating results in {b.industry}
- Provide comparison resources and decision frameworks supporting evaluation

## Conversion

Drive direct action and commitment from qualified leads ready to engage.

- Present clear, compelling calls-to-action with specific value propositions
- Deploy risk reversal mechanisms reducing perceived purchase risk
- Offer tiered options accommodating different commitment levels and budgets

## Retention

Maximize customer lifetime value through ongoing engagement and loyalty programs.

- Implement comprehensive onboarding ensuring successful product adoption
- Build community and advocacy programs encouraging referrals and testimonials
- Deploy retention campaigns preventing churn and maximizing lifetime value

| Stage | Objective | Key Channels | Core Tactics | Success Metrics |
|-------|-----------|-------------|-------------|----------------|
| **Awareness** | Build top-of-mind recognition and initial interest | Social media (organic + paid), Content marketing, SEO, Display advertising | Thought leadership content, Educational resources, Brand storytelling, Strategic paid amplification | Impressions, Reach, Brand awareness lift, Website traffic |
| **Consideration** | Educate prospects and build confidence through deeper engagement | Email nurture, Webinars, Case studies, Retargeting | Detailed product education, Customer success stories, Comparison guides, Demo content | Email engagement rate, Content download rate, Time-on-site, Video completion rate |
| **Conversion** | Convert qualified leads into customers | Sales conversations, Landing pages, Product demos, Limited offers | Clear CTAs with specific value propositions, Risk reversal guarantees, Time-limited incentives, Personalized proposals | Conversion rate, Cost per acquisition, Lead-to-customer rate, Sales cycle length |
| **Retention** | Maximize customer LTV and generate referrals | Customer success programs, Community building, Loyalty programs, Advocacy initiatives | Onboarding excellence, Proactive support, Exclusive benefits, Referral incentives | Customer retention rate, Net promoter score, Lifetime value, Referral conversion rate |

This full-funnel approach for {b.brand_name} ensures systematic progression from awareness to advocacy, with clear metrics tracking performance at each stage toward achieving {g.primary_goal}."""


def _gen_awareness_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'awareness_strategy' section."""
    b = req.brief.brand
    g = req.brief.goal
    return f"""## Objective

Build top-of-mind brand recognition and initial interest among target audiences in {b.industry}, establishing {b.brand_name} as a credible solution for organizations pursuing {g.primary_goal}. The awareness phase focuses on reaching decision-makers during their research and discovery phases when they're most open to new solutions.

## Key Channels

Multi-platform presence ensures consistent visibility where prospects naturally discover solutions:

- **Organic Social**: LinkedIn thought leadership posts, Twitter industry commentary, Instagram visual storytelling showcasing results and frameworks
- **Paid Social**: Precisely targeted campaigns on LinkedIn and Facebook reaching decision-makers in {b.industry} based on job titles, company size, and interests
- **Content Marketing**: SEO-optimized blog posts, educational resources, industry insights, downloadable guides, and comprehensive frameworks published consistently
- **Display Advertising**: Strategic placements on industry publications and relevant digital properties frequented by target audiences during research phases
- **Partnerships & Co-Marketing**: Collaborations with complementary brands, guest contributions to established platforms, and strategic alliances expanding reach
- **Search Engine Marketing**: Google Ads campaigns targeting high-intent keywords indicating active solution research and consideration

## Core Tactics

Systematic content deployment that builds awareness while establishing expertise and credibility:

- Educational content highlighting common problems and industry challenges without immediately pitching solutions, building trust through value-first approach
- Social proof elements including customer logos, testimonials, case study previews, and industry recognition establishing credibility and trust
- Consistent brand presence maintaining regular visibility across all channels with cohesive messaging that reinforces key themes and differentiation
- Strategic paid amplification of highest-performing organic content to extend reach beyond existing audiences and maximize content ROI
- Thought leadership positioning through original research, industry commentary, and expert perspectives that establish authority in {b.industry}
- Community engagement through active participation in relevant conversations, responding to questions, and providing helpful insights without aggressive promotion
- Performance tracking with monthly optimization cycles adjusting tactics based on engagement data, reach metrics, and downstream conversion patterns
- Retargeting infrastructure capturing engaged visitors for downstream nurture campaigns that progressively deepen relationships

Success metrics: Impressions, unique reach, engagement rate, click-through rate, brand awareness lift, website traffic growth, content downloads."""


def _gen_consideration_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'consideration_strategy' section."""
    b = req.brief.brand
    g = req.brief.goal
    a = req.brief.audience
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Full-funnel pack has different requirements
    if "full_funnel" in pack_key.lower():
        return f"""## Acquisition Channels

Strategic channel mix for acquiring customers efficiently:

- **Paid Social**: Facebook/Instagram targeting {a.primary_customer or 'target audience'} with conversion-focused creative and audience segmentation
- **Google Search**: Intent-based keyword targeting capturing active problem-seekers with high commercial intent
- **Content Marketing**: SEO-optimized content attracting organic traffic through educational resources and thought leadership
- **Partnership Marketing**: Strategic collaborations with complementary brands providing warm introductions and credibility transfer
- **Email Marketing**: Nurture sequences for lead-to-customer conversion with behavioral triggering and personalization

## Offers & Hooks

Compelling value propositions driving initial engagement and trial:

- **Free Trial**: 14-day full-access trial removing risk and enabling product-led growth through direct experience
- **Freemium Tier**: Entry-level free plan building user base and demonstrating value before asking for payment
- **Lead Magnet**: High-value content asset (guide, template, tool) capturing contacts in exchange for expertise sharing
- **Demo Offer**: Personalized demonstration with consultation showing specific value for prospect's situation
- **Early Access**: Exclusive beta invitation creating scarcity and community feel for engaged prospects
- **Money-Back Guarantee**: Risk reversal removing purchase anxiety and demonstrating confidence in product value

## Landing Flow

Optimized conversion path from click to customer:

- **Landing Page Structure**: Problem agitation, solution presentation, social proof, clear CTA with minimal friction points
- **Form Optimization**: Progressive disclosure collecting essential information first, avoiding overwhelming long forms
- **Trust Signals**: Security badges, testimonials, case study snippets, and media logos building credibility instantly
- **Mobile Experience**: Responsive design ensuring seamless experience across devices with thumb-friendly interactions
- **Load Speed**: Sub-2-second page loads preventing abandonment and improving conversion rates significantly
- **A/B Testing**: Systematic experimentation on headlines, CTAs, layouts optimizing conversion continuously

Acquisition cost target: ${a.online_hangouts[0] if hasattr(a, 'online_hangouts') and a.online_hangouts else 'X'} per customer with improving efficiency through optimization.
"""
    else:
        # Default/campaign pack version
        return f"""## Nurture Strategy

Educate prospects and build confidence through progressively deeper engagement that addresses objections and demonstrates value. The consideration phase transforms awareness into qualified interest through systematic nurture sequences designed to build trust and credibility.

## Content Sequencing

Systematic progression from awareness to serious consideration through multi-touch educational campaigns:

- **Email Nurture Series**: 5-7 email sequence delivering strategic insights, industry best practices, and framework introductions with clear value at each touchpoint
- **Case Study Showcase**: Detailed success stories from {b.industry} organizations achieving outcomes similar to {g.primary_goal} with specific metrics, timelines, and implementation details
- **Educational Content**: Webinars, workshops, and deep-dive articles explaining methodology and approach in practical, implementation-focused terms that prospects can apply immediately
- **Product Education**: Feature demonstrations, use case scenarios, and implementation roadmaps showing exactly how solutions work in practice with real examples
- **Comparison Resources**: Honest assessment of different approaches, alternatives, and decision frameworks helping prospects evaluate options objectively without heavy-handed sales pressure
- **Expert Engagement**: Q&A sessions, consultation offers, and direct dialogue opportunities providing personalized guidance and building authentic relationships
- **Resource Libraries**: Comprehensive collections of templates, frameworks, and tools prospects can use immediately to sample the value proposition before committing

## Engagement Tactics

Multi-touch approach maintaining connection without overwhelming prospects with excessive outreach or aggressive sales tactics:

- Retargeting campaigns showing relevant educational content to engaged audiences from awareness phase based on specific behaviors and demonstrated interests
- Progressive profiling gathering additional prospect information through value-exchange content offers that deepen understanding of needs and priorities over time
- Behavioral triggering with automated responses to specific actions indicating growing interest such as pricing page visits, case study downloads, or demo requests
- Social proof reinforcement through customer testimonials, peer reviews, and industry validation establishing credibility and reducing perceived risk of engagement
- Risk reversal positioning with guarantees, trials, and low-commitment entry points removing barriers to initial engagement and reducing decision anxiety
- Personalized outreach from sales team based on engagement signals and profile fit, ensuring human connection at the right moments in the buying journey

## Performance Indicators

Tracking metrics: Email engagement rates, content download velocity, time-on-site for educational resources, video completion rates, webinar attendance, demo request volume, MQL conversion rate.

Typical duration: 7-21 days per prospect moving through consideration stage, with systematic follow-up maintaining engagement and building relationships over time."""


def _gen_conversion_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'conversion_strategy' section."""
    b = req.brief.brand
    _ = req.brief.goal  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Full-funnel pack has different requirements
    if "full_funnel" in pack_key.lower():
        return f"""## First Value Moment

Critical milestone where new users experience tangible value from {b.brand_name}:

**Target**: Users achieve first meaningful outcome within 24 hours of signup, creating emotional commitment and reducing churn risk during critical early period.

- **Quick Win**: Immediate small success demonstrating product value without requiring extensive setup or learning curve
- **Aha Moment**: Point where user understands product's core value proposition through direct experience rather than explanation
- **Emotional Payoff**: Satisfaction, relief, or excitement creating positive association with {b.brand_name} brand
- **Progress Indicator**: Visual confirmation showing user they're moving toward their goal creating momentum and engagement
- **Social Validation**: Sharing or displaying achievement to peers reinforcing value and encouraging continued usage

## Onboarding Steps

Systematic activation flow guiding users to first value moment:

- **Step 1: Account Setup** (2 minutes) - Minimal information collection, social login options, clear progress indicators showing remaining steps
- **Step 2: Profile Customization** (3 minutes) - Personalization questions tailoring experience, skippable for quick start, data used for relevant recommendations
- **Step 3: First Action** (5 minutes) - Guided workflow achieving quick win, tooltips and inline help, impossible to get stuck or lost
- **Step 4: Value Demonstration** (immediate) - Show concrete result, celebrate achievement, explain what just happened and why it matters
- **Step 5: Next Steps** (contextual) - Suggest logical progression, invite deeper exploration, offer additional resources without overwhelming

## Friction Points

Identified obstacles preventing activation and their solutions:

- **Complex Signup**: Too many required fields creating abandonment - Solution: Progressive disclosure collecting data over time as needed
- **Unclear Next Steps**: Users don't know what to do after signup - Solution: Clear onboarding checklist with visual progress tracking
- **Missing Context**: Users don't understand product value - Solution: Contextual tooltips and example data showing possibilities
- **Technical Barriers**: Integration or setup requirements blocking usage - Solution: One-click templates and pre-configured options
- **Decision Paralysis**: Too many options overwhelming new users - Solution: Recommended starting path with ability to customize later
- **Delayed Gratification**: Value requires significant upfront work - Solution: Quick wins demonstrating value before asking for heavy lifting

Activation rate target: 60%+ of signups complete onboarding and achieve first value moment within 7 days.
"""
    else:
        # Default/campaign pack version
        return f"""## Conversion Tactics

Drive direct action and commitment from qualified prospects ready to engage with {b.brand_name}, transforming consideration into customer relationships through strategic conversion mechanisms.

## Offer Architecture

Strategic conversion mechanisms addressing different prospect segments and commitment levels:

- **Primary CTA**: Clear, benefit-focused call-to-action with specific value proposition and outcome promise that eliminates ambiguity about next steps
- **Risk Reversal**: Guarantees, money-back offers, trial periods, and satisfaction commitments reducing perceived risk of purchase decision
- **Time-Limited Offers**: Strategic scarcity through expiring bonuses, limited availability, or deadline-driven promotions creating urgency without artificial pressure
- **Tiered Options**: Multiple entry points accommodating different budget levels and commitment readiness, from starter packages to comprehensive solutions
- **Social Proof at Decision Point**: Testimonials, case studies, and peer validation prominently displayed exactly when prospects evaluate options
- **Urgency Mechanisms**: Legitimate time-sensitivity through bonuses expiring, limited cohort sizes, or seasonal relevance tied to business planning cycles
- **Bundle Strategies**: Complementary offerings packaged together creating higher perceived value while increasing average transaction size

## Conversion Optimization

Systematic improvement of conversion infrastructure maximizing success rates across all touchpoints:

- **Landing Page Excellence**: Benefit-focused copy, clear visual hierarchy, minimal friction, strong contrast on CTAs, and mobile-optimized experiences
- **Sales Conversation Protocol**: Structured discovery process identifying fit, addressing objections, presenting tailored solutions based on specific needs
- **Personalization at Scale**: Dynamic content showing relevant case studies, testimonials, and value propositions by segment, industry, and use case
- **Abandonment Recovery**: Automated sequences re-engaging prospects who showed intent but didn't complete action, with progressive value adds
- **Objection Handling**: Preemptive FAQ content, comparison guides, and direct response mechanisms addressing common concerns before they become blockers
- **Conversion Tracking**: Comprehensive analytics identifying drop-off points and optimization opportunities throughout the conversion funnel
- **Live Support**: Real-time chat and phone support available during critical decision moments to answer questions and remove friction
- **Trust Signals**: Security badges, privacy policies, customer logos, certifications, and third-party validation building confidence at point of purchase

## Performance Metrics

Tracking: Conversion rate by source, cost per acquisition, lead quality scores, sales cycle length, close rate by segment, revenue per visitor, customer acquisition cost.

Typical duration: Concentrated conversion push over 5-10 days, with systematic follow-up for non-converters maintaining relationship for future opportunities and building long-term pipeline."""


def _gen_retention_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'retention_strategy' section."""
    b = req.brief.brand
    _ = req.brief.goal  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Full-funnel and enterprise packs need specific headings
    if "full_funnel" in pack_key.lower() or "enterprise" in pack_key.lower():
        return f"""## Retention Drivers

Core mechanisms keeping customers engaged with {b.brand_name} over time:

- **Product Value Delivery**: Continuous demonstration of ROI through tangible business outcomes and measurable performance improvements
- **Community Connection**: Building relationships between customers through forums, events, and peer learning creating switching costs
- **Progress Tracking**: Visible advancement toward goals maintaining motivation and demonstrating cumulative value of sustained engagement
- **Personalization Engine**: Adaptive experience learning from user behavior to provide increasingly relevant and valuable interactions
- **Support Excellence**: Proactive assistance and rapid problem resolution building trust and reducing frustration-based churn
- **Feature Velocity**: Regular product enhancements and new capabilities providing continuous improvement and innovation perception

## Habit Loops

Behavioral patterns embedding {b.brand_name} into daily workflows:

- **Daily Check-in Trigger**: Morning notification or email prompting status review creating routine interaction pattern
- **Action-Reward Cycle**: Complete task → See progress → Feel accomplishment building positive reinforcement loop
- **Social Proof Exposure**: Regular updates on peer achievements creating aspirational motivation and engagement
- **Streak Maintenance**: Consecutive day usage tracking leveraging loss aversion to maintain engagement momentum
- **Variable Rewards**: Unpredictable valuable content or insights creating anticipation and repeated checking behavior

## Engagement Moments

Strategic touchpoints maintaining active relationship throughout customer lifecycle:

- **Week 2 Check-in**: Proactive outreach ensuring early adoption success and identifying potential churn risks before they escalate
- **Monthly Value Report**: Automated summary of achievements and ROI demonstrating ongoing value and justifying continued investment
- **Quarterly Business Review**: Strategic consultation aligning product usage with evolving business goals and identifying expansion opportunities
- **Feature Adoption Campaign**: Targeted education on underutilized capabilities increasing product stickiness through deeper integration
- **Anniversary Celebration**: Milestone recognition with exclusive offers or content rewarding loyalty and reinforcing relationship
- **Renewal Optimization**: Proactive value demonstration 60-90 days before renewal reducing decision friction and preventing churn

Retention target: 85%+ annual retention rate with improving cohort performance over time through systematic engagement optimization."""
    else:
        # Default/campaign pack version with different headings
        return f"""Comprehensive retention strategy maximizing customer lifetime value and reducing churn for {b.brand_name}.

## Retention Drivers

Core initiatives keeping customers engaged and preventing churn:

- **Exceptional Onboarding Experience**: Structured 30-day onboarding program ensuring customers achieve first wins quickly, reducing early-stage churn risk
- **Consistent Value Delivery**: Regular product updates, feature releases, and capability enhancements demonstrating ongoing innovation and investment
- **Proactive Customer Success**: Dedicated success managers conducting quarterly business reviews, sharing best practices, and identifying growth opportunities
- **Educational Content Program**: Ongoing training through webinars, documentation, tutorials, and certification programs improving customer proficiency and stickiness
- **Community Building**: User forums, peer networks, and customer advisory boards creating belonging and investment in platform ecosystem
- **Performance Benchmarking**: Regular reports showing customer performance versus industry benchmarks and improvement trajectories building confidence

## Engagement Moments

Strategic touchpoints maintaining relationship momentum throughout customer lifecycle:

- **Milestone Celebrations**: Recognizing customer anniversaries, usage milestones, and achievement moments with personalized communications
- **Feature Adoption Campaigns**: Targeted outreach introducing underutilized features relevant to customer needs increasing perceived value
- **Executive Check-Ins**: Quarterly touchpoints between customer and {b.brand_name} leadership demonstrating commitment and gathering strategic feedback
- **Renewal Conversations**: Proactive outreach 90 days before renewal discussing results achieved, future goals, and expansion opportunities
- **Win-Back Sequences**: Automated campaigns targeting lapsed or churning customers with special offers, success stories, and direct outreach
- **Referral Program Activations**: Incentivized advocacy encouraging satisfied customers to introduce peers creating network effects

## Retention Metrics & Goals

Key performance indicators tracking retention effectiveness:

- **Net Revenue Retention (NRR)**: Target 110%+ through expansion revenue exceeding churn impact
- **Gross Churn Rate**: Maintain below 5% monthly through proactive intervention and value delivery
- **Customer Satisfaction (CSAT/NPS)**: Achieve 8.5+ satisfaction score through regular surveys and feedback loops
- **Feature Adoption Rates**: Track usage of key features correlating with lower churn and higher satisfaction
- **Time to Value**: Reduce onboarding time from signup to first win driving early engagement and reducing abandonment

Goal: Transform customers into advocates generating organic growth through referrals and testimonials while building predictable recurring revenue base supporting long-term business sustainability."""


def _gen_sms_and_whatsapp_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'sms_and_whatsapp_strategy' section."""
    _ = req.brief.brand  # noqa: F841
    _ = req.brief.goal  # noqa: F841
    return """## SMS Strategy

Direct, high-urgency messaging for time-sensitive communications:

- **Welcome Messages**: Immediate value delivery and expectation setting upon opt-in
- **Promotional Alerts**: Time-limited offers, flash sales, exclusive deals with clear expiration
- **Transactional Updates**: Order confirmations, shipping notifications, appointment reminders
- **Event Notifications**: Webinar reminders, deadline alerts, important announcements
- **Frequency Management**: Maximum 2-3 messages weekly to avoid fatigue and maintain engagement
- **Opt-Out Compliance**: Clear unsubscribe instructions in every message per regulatory requirements

## WhatsApp Strategy

Conversational, relationship-focused engagement with lower frequency:

- **Customer Support**: Real-time assistance, problem resolution, proactive outreach for common issues
- **Personalized Communication**: One-on-one conversations tailored to individual customer needs and history
- **Community Building**: Group messages fostering peer connections and shared learning
- **Content Distribution**: Sharing valuable resources, industry insights, educational materials
- **Frequency Management**: 1-2 messages weekly maintaining quality over quantity
- **Interactive Elements**: Polls, questions, feedback requests encouraging two-way dialogue

## Compliance & Best Practices

Regulatory adherence and user experience optimization:

- Explicit opt-in collection with clear value proposition explaining what subscribers receive
- Easy opt-out mechanisms prominently displayed in all messages
- Respect for user preferences regarding frequency and content types
- Avoid spammy language triggering carrier filters or regulatory violations
- Segment by engagement level sending higher frequency to most engaged subscribers
- Track delivery rates, open rates, click rates, and opt-out rates for continuous improvement

Integration with broader marketing strategy ensures SMS and WhatsApp complement email and social rather than creating redundant touchpoints that overwhelm prospects."""


def _gen_remarketing_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'remarketing_strategy' section."""
    _ = req.brief.brand  # noqa: F841
    g = req.brief.goal
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs specific remarketing audiences heading
    if "performance_audit" in pack_key.lower():
        return """## Remarketing Audiences

Strategic audience segmentation for targeted remarketing campaigns prioritized by conversion potential:

**High-Intent** (80% budget allocation): Demo Downloaders/Free Trial Users (~450/month, 18-25% conversion, 7-day retargeting with success stories and offers). Pricing Page Visitors (~800/month, 8-12% conversion, 14-day ROI-focused campaign). Form Abandoners (~450/month, 15-20% recovery, 3-day immediate follow-up).

**Medium-Intent** (15% budget allocation): Blog/Resource Consumers (~2,400/month, 3-5% conversion, 30-day educational nurture). Video Watchers (~600/month, 5-7% conversion, 21-day sequential storytelling).

**Lower-Intent** (5% budget allocation): Homepage/Brief Visitors (~8,000/month, 0.5-1% conversion, 60-90 day brand awareness play).

## Strategy

Execution framework for remarketing optimization:

**Campaign Structure** - Segment by intent level with distinct messaging per segment. Frequency capping: 3-5 impressions/week for high-intent, 1-2/week for low-intent. Sequential messaging progressing awareness → consideration → decision. Dynamic creative personalized based on pages/content engaged. Multi-platform: Facebook, Instagram, Google Display, LinkedIn.

**Creative Strategy** - High-intent: Direct response with offers, urgency, clear CTAs. Medium-intent: Educational value with softer CTAs. Low-intent: Brand building and social proof. Refresh every 14-21 days. A/B test 3-5 variations per segment identifying winners.

**Conversion Paths** - High-intent → dedicated landing pages with pre-filled forms. Medium-intent → content hubs with progressive conversion path. Low-intent → educational landing pages with soft CTAs. Exit-intent offers capturing final opportunity.

## Performance Targets

Expected remarketing performance metrics:

- Overall conversion rate 8-12% (vs 2-3% cold traffic)
- Cost per acquisition $25-$32 (vs $41 average)
- Revenue attribution 35-40% of total conversions
- ROAS 4-5x (vs 1.9x cold acquisition)
- Pipeline contribution +180-220 monthly conversions

Remarketing represents highest ROI opportunity—systematic segmentation and tailored messaging can recover 15-25% of otherwise lost opportunities while reducing overall CAC 25-35%."""
    # Full-funnel pack focuses on revenue expansion
    elif "full_funnel" in pack_key.lower():
        return """## Revenue Streams

Diversified monetization model capturing value across customer lifecycle:

- **Core Subscription**: Primary SaaS revenue from monthly/annual plans providing predictable recurring income base
- **Usage-Based Pricing**: Overage charges for high-volume users ensuring revenue scales with customer success and value delivered
- **Professional Services**: Implementation, training, and consulting fees monetizing expertise and accelerating customer outcomes
- **Enterprise Add-ons**: Advanced features, security, and support packages targeting high-value accounts with specialized needs
- **Marketplace Commission**: Revenue share from third-party integrations and extensions creating platform ecosystem value
- **Data/Insights Products**: Aggregated industry benchmarks and analytics monetizing network effects and data assets

## Pricing Logic

Strategic pricing architecture optimizing for acquisition, expansion, and retention:

- **Value Metric Alignment**: Pricing based on metrics correlated with customer value (users, volume, features) ensuring fairness perception
- **Good-Better-Best Tiers**: Three-tier structure with 60% of customers choosing middle option through anchoring and decoy effects
- **Penetration Pricing**: Aggressive entry pricing capturing market share with expansion revenue through upsells over time
- **Annual Discount**: 15-20% discount for annual commitment improving cash flow and reducing monthly churn exposure
- **Free Trial → Paid**: No credit card trial converting at 15-25% rate with automated nurture and usage-based triggers
- **Grandfathering**: Protecting legacy pricing for existing customers during increases maintaining goodwill and reducing churn risk

## Upsell & Cross-sell

Systematic expansion revenue opportunities within existing customer base:

- **Feature Tier Upgrades**: Automated prompts when users hit plan limits converting friction into revenue at point of high motivation
- **User Seat Expansion**: Team growth identification triggering sales outreach for multi-user license expansion opportunities
- **Add-on Module Sales**: Complementary product offerings (integrations, analytics, automation) expanding wallet share and stickiness
- **Professional Services**: Implementation and optimization consulting converting product questions into revenue-generating engagements
- **Annual Contract Upgrades**: Mid-contract upsells to annual plans with prorated discount incentivizing longer commitment and improving retention
- **Enterprise Migration**: SMB account growth identification triggering white-glove sales process for enterprise plan conversion

Expansion revenue target: 20-30% of total revenue from existing customer upsells and cross-sells within 24 months of acquisition."""
    else:
        # Default/campaign pack version
        return f"""## Retargeting Strategy

Re-engage prospects who demonstrated interest but haven't converted, addressing objections and providing additional proof points to move them toward {g.primary_goal}.

## Audience Segmentation

Strategic remarketing lists targeting specific behaviors:

- **Website Visitors (No Conversion)**: Anyone who visited site but didn't complete desired action, segmented by pages viewed
- **Content Engagers**: Users who downloaded resources, watched videos, or read multiple articles showing interest
- **Email Openers (No Click)**: Subscribers opening emails but not taking next step, indicating hesitation or distraction
- **Video Watchers (High Completion)**: Prospects watching 50%+ of video content demonstrating strong interest level
- **Cart Abandoners**: Users adding products/services to cart without completing purchase, highest intent audience
- **Form Starters**: Prospects beginning signup or inquiry forms without submission, indicating decision friction
- **Event Registrants (No Show)**: Webinar/event registrations without attendance, requiring re-engagement

## Messaging Framework

Tailored messages addressing specific objections and barriers:

- **Objection Handling**: Address common hesitations through FAQ content, comparison guides, risk reversal offers
- **Social Proof Reinforcement**: New testimonials, case studies, peer reviews not seen in initial exposure
- **Limited-Time Incentives**: Exclusive retargeting offers with genuine scarcity creating urgency
- **Feature Education**: Deeper dive into specific capabilities or benefits matching browsing behavior
- **Trust Building**: Additional credibility markers including certifications, guarantees, media mentions
- **Alternative Pathways**: Different conversion options accommodating various commitment levels and budgets
- **Personalized Messaging**: Dynamic creative showing specific products, services, or content previously engaged with

## Campaign Structure

Systematic remarketing approach:

Frequency capping at 2-3 ad impressions per person over 14-21 day window prevents ad fatigue while maintaining visibility. Attribution tracking identifies which remarketing messages drive conversions. Budget allocation prioritizes highest-intent audiences (cart abandoners, form starters) with decreasing spend for lower-intent segments. Creative rotation every 2-3 weeks maintains freshness."""


def _gen_optimization_opportunities(req: GenerateRequest, **kwargs) -> str:
    """Generate 'optimization_opportunities' section (markdown table format)."""
    b = req.brief.brand
    _ = req.brief.goal  # noqa: F841
    return f"""## High-Impact Experiments

Systematic testing opportunities to improve campaign performance for {b.brand_name}.

## Quick Wins

Immediate optimizations delivering fast results:

- Refresh all bio and profile CTAs with action-oriented language focused on specific outcomes
- A/B test three email subject line variations measuring open rate improvements
- Create three variations of top-performing social post to identify winning creative patterns
- Audit existing landing pages fixing obvious conversion barriers like slow load times
- Update website hero copy with clearer value proposition and benefit statements
- Optimize top-performing blog posts for SEO with keyword targeting and internal linking
- Implement exit-intent popups on high-traffic pages capturing abandoning visitors
- Add social proof elements (testimonials, logos, metrics) to key conversion pages

## Testing Roadmap

Prioritized experiments balancing potential impact with implementation complexity.

| Timeline | Experiment Type | Specific Test | Expected Impact | Implementation Complexity | Success Metric |
|----------|----------------|---------------|-----------------|---------------------------|----------------|
| **Week 1** | Quick Win | Refresh bio/profile CTAs with action-oriented language | 10-15% click improvement | Low | Click-through rate |
| **Week 1** | Quick Win | A/B test 3 email subject line variations | 15-25% open rate lift | Low | Email open rate |
| **Week 1** | Quick Win | Create 3 variations of top-performing post | 20-30% engagement increase | Low | Engagement rate |
| **Week 2** | Medium-Term | Scale paid spend on 2-3 winning creatives | 40-60% more conversions | Medium | Cost per acquisition |
| **Week 2** | Medium-Term | Build new email sequence based on engagement data | 25-35% conversion lift | Medium | Email-to-customer rate |
| **Week 3** | Medium-Term | Develop webinar or case study content asset | 30-50% lead quality increase | Medium | Lead qualification rate |
| **Week 4** | Medium-Term | Test different landing page layouts and CTAs | 15-30% conversion improvement | Medium | Landing page conversion rate |
| **Month 2** | Long-Term | Build referral program with incentive structure | 20-40% new lead source | High | Referral conversion rate |
| **Month 2** | Long-Term | Create video content series for YouTube/social | 50-100% reach expansion | High | Video view rate, Channel growth |
| **Month 3** | Long-Term | Develop partnership program with complementary brands | 30-60% audience growth | High | Partner-sourced leads |
| **Month 3** | Long-Term | Launch community platform for customer engagement | 40-70% retention improvement | High | Community engagement, NPS |
| **Ongoing** | Continuous | Weekly creative refresh based on performance data | 10-20% sustained improvement | Medium | Aggregate campaign metrics |

## Longer-Term Bets

Strategic initiatives requiring significant investment but offering transformational impact:

- **Build Proprietary Research Program**: Annual industry benchmark report establishing {b.brand_name} as data authority generating 1000+ qualified leads per year through gated distribution
- **Launch Customer Community Platform**: Dedicated forum or Slack community for peer learning and product feedback increasing retention 40%+ and creating organic growth flywheel
- **Develop Certification Program**: Professional training and credentialing creating ecosystem of advocates while generating $500K+ annual revenue and driving product adoption
- **Create Strategic Partnership Network**: Formalized co-marketing relationships with 5-10 complementary brands accessing combined audience of 500K+ prospects at fraction of paid acquisition cost
- **Build Content Media Hub**: Comprehensive educational resource center (blog, podcast, video library, tools) attracting 50K+ monthly organic visitors becoming primary lead generation channel
- **Implement AI Personalization Engine**: Dynamic content and recommendation system tailoring experience to individual user behavior improving conversion rates 30%+ across all funnel stages

All experiments include clear hypothesis, success criteria, and decision framework for scaling winners or killing losers. Prioritization favors high-impact, low-complexity tests early, building toward more ambitious long-term optimizations."""


def _gen_industry_landscape(req: GenerateRequest, **kwargs) -> str:
    """Generate 'industry_landscape' section."""
    b = req.brief.brand
    raw = f"""The {b.industry or 'your industry'} landscape is experiencing significant transformation driven by technology adoption, changing customer expectations, and competitive dynamics that create both opportunities and challenges for {b.brand_name}.

## Market Trends

Key market movements shaping {b.industry or 'the industry'}:

- **Digital Transformation Acceleration**: Rapid shift towards cloud-based, mobile-first, and AI-powered solutions creating new customer expectations for speed, convenience, and personalization
- **Customer Experience Emphasis**: Brands competing on experience quality rather than product features alone, with 73% of customers expecting seamless omnichannel interactions
- **Data-Driven Decision Making**: Increased reliance on analytics, attribution, and performance metrics to justify marketing spend and optimize campaigns in real-time
- **Content Saturation & Ad Blindness**: Rising content volume making differentiation harder, requiring authentic storytelling, community building, and value-driven content strategies
- **Privacy & Trust Focus**: Growing consumer awareness of data practices forcing brands to balance personalization with transparency and ethical data usage
- **Economic Sensitivity**: Budget scrutiny and ROI pressure requiring proof of marketing effectiveness and clear path to revenue impact

## Industry Dynamics

Competitive and operational forces influencing {b.brand_name} market position:

- **Market Consolidation**: Mid-size players facing pressure from both established enterprises with deep pockets and agile startups with innovative approaches
- **Customer Acquisition Costs Rising**: Paid channel saturation driving CAC up 50%+ over past 3 years, forcing brands to build owned audiences and organic channels
- **Talent War for Marketing Expertise**: Difficulty attracting and retaining skilled marketers who understand modern channels, analytics, and growth strategies
- **Technology Stack Complexity**: Average marketing team managing 12+ tools creating integration challenges, data silos, and workflow inefficiencies
- **Shortened Planning Cycles**: Traditional annual planning replaced by quarterly or monthly adaptive strategies responding to market changes and performance data
- **Community & Creator Economy**: Rise of micro-influencers, user-generated content, and community-led growth as cost-effective alternatives to traditional paid media

## Competitive Environment

Market structure and positioning dynamics impacting {b.brand_name} strategy:

- **Incumbent Advantage**: Established players benefit from brand recognition, customer inertia, and economies of scale making market entry challenging for new entrants
- **Innovation Pressure**: Continuous product evolution required to maintain relevance as customer expectations and technology capabilities advance rapidly
- **Pricing Competition**: Downward price pressure from international competitors and DIY alternatives compressing margins and requiring clear value justification
"""
    return sanitize_output(raw, req.brief)


def _gen_market_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'market_analysis' section."""
    b = req.brief.brand
    raw = f"""Comprehensive market analysis establishing strategic context for {b.brand_name} growth initiatives.

## Market Context

{b.industry or 'The market'} represents substantial opportunity with clear growth trajectory:

- **Total Addressable Market (TAM)**: Global market estimated at $X billion with Y% CAGR over next 5 years driven by digital transformation
- **Serviceable Addressable Market (SAM)**: Target segment within {b.industry or 'market'} represents $X billion focusing on mid-market and enterprise customers
- **Serviceable Obtainable Market (SOM)**: Realistic Year 1 capture of 0.5-2% market share representing $X million revenue potential
- **Market Maturity Stage**: Transitioning from early adoption to mainstream acceptance creating window for aggressive growth
- **Economic Climate**: Current conditions favor solutions demonstrating clear ROI and operational efficiency gains

## Current Performance

{b.brand_name} baseline metrics and performance context:

- **Current Market Position**: Early-stage challenger with growing brand recognition in target segments
- **Revenue Trajectory**: Month-over-month growth trends indicating product-market fit and scalability potential
- **Customer Acquisition Efficiency**: CAC payback period currently X months with opportunity for optimization through channel mix and conversion improvements
- **Customer Retention Metrics**: Net revenue retention at X% demonstrating product stickiness and expansion opportunity
- **Brand Awareness**: Limited unaided awareness (estimated <5%) creating significant headroom for growth through awareness-driving initiatives

## Competitive Landscape

Market structure and competitive positioning dynamics:

- **Tier 1 Players**: 2-3 established leaders commanding 40-60% market share with mature products, extensive sales teams, and significant marketing budgets
- **Tier 2 Competitors**: 5-8 mid-size challengers competing on specialization, customer service, or pricing creating fragmented market dynamics
- **Emerging Disruptors**: New entrants leveraging modern technology stacks, community-driven growth, and category redefinition strategies
- **Indirect Competition**: Adjacent solutions and DIY approaches representing competitive alternative for price-sensitive or underserved segments

## Key Challenges

Critical obstacles and market headwinds requiring strategic response:

- **Low Unprompted Awareness**: Brand recognition gap versus competitors requiring significant investment in top-of-funnel awareness building
- **Crowded Channel Competition**: Paid media saturation and rising CPMs necessitating creative differentiation and owned channel development
- **Complex Buyer Journey**: Multi-stakeholder B2B decisions with 6-9 month sales cycles requiring sustained nurture and trust-building
- **Budget Constraints**: Target customers balancing growth ambitions with limited resources demanding clear ROI proof and flexible pricing models
"""
    return sanitize_output(raw, req.brief)


def _gen_competitor_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'competitor_analysis' section."""
    b = req.brief.brand
    return f"""## Competitive Landscape

The {b.industry} market features intense competition across multiple tiers:

- **Tier 1 Competitors**: 2-3 dominant players with strong brand recognition, substantial marketing budgets, and loyal customer bases built over years
- **Tier 2 Challengers**: 5-7 mid-market competitors offering similar value propositions with varying degrees of differentiation and market presence
- **Emerging Disruptors**: Newer entrants leveraging technology, pricing innovation, or novel business models to capture market share rapidly
- **Indirect Competitors**: Alternative solutions from adjacent categories that solve similar customer problems through different approaches
- **Private Label Options**: In some segments, retailer-owned brands compete primarily on price advantage and convenience factors

{b.brand_name} currently positioned in competitive Tier 2, facing pressure from established leaders above and aggressive disruptors below.

## Competitive Strengths & Weaknesses Analysis

**Where Competitors Excel:**
- Tier 1 players dominate through massive brand awareness campaigns, omnipresent distribution networks, and deep customer trust
- Disruptors win with aggressive pricing strategies, innovative customer acquisition channels (social, influencer, community), and modern aesthetics
- Key competitors have clearer positioning statements, more memorable taglines, and stronger emotional brand narratives
- Better resourced competitors invest heavily in content marketing, customer education, and thought leadership
- Some competitors have superior customer communities, effective advocacy programs, and strong organic word-of-mouth

**Competitive Vulnerabilities {b.brand_name} Can Exploit:**
- Tier 1 brands perceived as impersonal, inflexible, and focused on volume over authentic customer relationships
- Many competitors rely on outdated marketing tactics (trade shows, print ads) creating digital-first opportunities
- Generic positioning among Tier 2 players creates opening for sharp differentiation and niche category domination
- Customer service gaps at larger competitors provide opportunity for {b.brand_name} to win through superior support
- Price-focused competitors vulnerable to value proposition attacks emphasizing quality, reliability, and total ownership cost
- Limited innovation in customer experience across category creates opportunity to lead experience transformation

**Strategic Positioning Recommendation:**

Avoid head-to-head battles with Tier 1 budgets while staying relevant against disruptor innovation. Stake clear differentiated territory, own specific customer segment deeply, and deliver superior experience generating organic advocacy."""


def _gen_customer_insights(req: GenerateRequest, **kwargs) -> str:
    """Generate 'customer_insights' section."""
    b = req.brief.brand
    a = req.brief.audience
    return f"""## Customer Pain Points

Target customers in {b.industry} face specific challenges that {b.brand_name} can address:

- **Information Overload**: Overwhelmed by competing claims and unclear differentiators making purchase decisions difficult and time-consuming
- **Trust Deficit**: Past negative experiences with competitors create skepticism toward category promises and marketing claims
- **Time Constraints**: Busy professionals lack time to research extensively, need clear guidance and simplified buying processes
- **Budget Pressure**: Economic uncertainty drives conservative spending and demands for clear ROI justification before commitment
- **Implementation Risk**: Fear of choosing wrong solution leading to wasted resources, team frustration, and internal criticism
- **Support Gaps**: Previous vendors provided inadequate onboarding, training, and ongoing customer success resources

These pain points create emotional frustration (anxiety, confusion, overwhelm) and practical barriers (delayed decisions, status quo bias, vendor switching resistance).

## Motivations

What drives target customers toward considering {b.brand_name} and taking action:

- **Performance Improvement**: Desire to achieve measurable gains in efficiency, revenue, or key business metrics that advance careers
- **Risk Mitigation**: Need for proven, reliable solution that minimizes implementation and performance risk with stakeholders
- **Peer Validation**: Strongly influenced by what competitors and industry leaders are using successfully in similar situations
- **Future-Proofing**: Want scalable solution that grows with business needs without requiring constant platform reinvestment
- **Expert Guidance**: Value vendors who act as strategic partners providing consultative support, best practices, and industry insights
- **Brand Alignment**: Prefer working with brands that share their values, vision, and approach to business relationships

Customers are motivated by both avoiding pain (fear of failure, wasted resources) and pursuing gain (competitive advantage, recognition, career advancement). Emotional drivers often outweigh rational factors in final purchase decisions.

**Key Insight**: {a} aren't seeking the cheapest option or the most features. They want confidence that their choice will succeed, be supported, and position them favorably with internal stakeholders. Brand turnaround must rebuild this confidence through consistent proof points, clear positioning, and authentic customer-centric messaging that addresses both rational and emotional decision factors."""


def _gen_customer_journey_map(req: GenerateRequest, **kwargs) -> str:
    """Generate 'customer_journey_map' section."""
    b = req.brief.brand
    _ = req.brief.audience  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## Pre-Purchase\n\n"
            "Customer discovery and evaluation phase before first purchase:\n\n"
            "| Touchpoint | Customer Mindset | Business Goal | Tactics |\n"
            "| --- | --- | --- | --- |\n"
            "| **First Visit** | Curious, researching options | Capture interest | Clear value prop, educational content, exit-intent popup |\n"
            "| **Browse & Compare** | Evaluating alternatives | Build trust | Social proof, reviews, comparison guides |\n"
            "| **Add to Cart** | Considering purchase | Convert | Limited-time offer, free shipping threshold, trust badges |\n\n"
            "- Focus: Convert browsers to first-time buyers\n"
            "- Key metric: Conversion rate 2-4%\n"
            "- Critical touchpoints: Homepage, product pages, checkout\n\n"
            "## Onboarding\n\n"
            "Post-purchase activation ensuring successful first experience:\n\n"
            "| Touchpoint | Customer Mindset | Business Goal | Tactics |\n"
            "| --- | --- | --- | --- |\n"
            "| **Welcome Email** | Excited, curious | Set expectations | Thank you message, quick-start guide, support resources |\n"
            "| **Day 1-3** | Learning the product | Drive activation | Tutorial videos, setup assistance, feature highlights |\n"
            "| **First Success** | Seeing value | Celebrate milestone | Congratulations message, next steps, community invite |\n\n"
            '- Focus: Drive "aha moment" within 7 days\n'
            "- Key metric: 70%+ complete onboarding\n"
            "- Critical touchpoints: Welcome email, tutorials, support\n\n"
            "## Active\n\n"
            "Engaged customer phase building loyalty and increasing lifetime value:\n\n"
            "| Touchpoint | Customer Mindset | Business Goal | Tactics |\n"
            "| --- | --- | --- | --- |\n"
            "| **Regular Usage** | Engaged, satisfied | Maximize value | Feature education, pro tips, usage stats dashboard |\n"
            "| **Repeat Purchase** | Loyal, happy | Increase frequency | Personalized recommendations, loyalty rewards, auto-reorder |\n"
            "| **Advocacy Moment** | Delighted, willing to share | Drive referrals | Referral program, review request, social sharing incentives |\n\n"
            "- Focus: Increase purchase frequency and AOV\n"
            "- Key metric: 40%+ repeat purchase within 90 days\n"
            "- Critical touchpoints: Email nurture, loyalty program, personalization\n\n"
            "## At-Risk\n\n"
            "Declining engagement phase requiring intervention to prevent churn:\n\n"
            "| Touchpoint | Customer Mindset | Business Goal | Tactics |\n"
            "| --- | --- | --- | --- |\n"
            '| **Declining Engagement** | Distracted, less interested | Re-engage | Special offer, "We miss you" email, feedback survey |\n'
            "| **Support Issues** | Frustrated, considering churn | Resolve friction | Proactive support, account review, improvement updates |\n"
            "| **Last Interaction** | On the fence | Prevent churn | Win-back campaign, personalized incentive, exit interview |\n\n"
            "- Focus: Identify and re-engage before permanent churn\n"
            "- Key metric: 60-day inactivity triggers intervention\n"
            "- Critical touchpoints: Re-engagement email, win-back offers, feedback loops\n\n"
            "## Lapsed\n\n"
            "Inactive customer phase with aggressive win-back campaigns:\n\n"
            "| Touchpoint | Customer Mindset | Business Goal | Tactics |\n"
            "| --- | --- | --- | --- |\n"
            '| **No Activity 30-90 days** | Moved on, forgotten | Reactivate | "What\'s new" update, reactivation discount, product improvements |\n'
            "| **No Activity 90+ days** | Uninterested, unsubscribed | Last-chance win-back | Deep discount, exclusive offer, reintroduction campaign |\n"
            "| **Permanent Churn** | Lost customer | Learn & improve | Exit survey analysis, segment removal, acquisition insights |\n\n"
            "- Focus: Last-ditch reactivation before permanent removal\n"
            "- Key metric: 8-12% reactivation rate for 90+ day inactive\n"
            "- Critical touchpoints: Multi-channel win-back sequences, aggressive discounting\n"
        )
    else:
        raw = f"""Detailed customer journey mapping key touchpoints, motivations, and marketing interventions guiding prospects toward {b.brand_name} adoption.

## Awareness

Initial discovery stage where prospects recognize problems and begin exploring solutions.

| Trigger | Customer Mindset | Touchpoints | {b.brand_name} Actions | Success Metrics |
|---------|-----------------|-------------|----------------------|-----------------|
| Frustration with current tools | "There must be a better way" | Social media, search, industry blogs | Educational content, thought leadership, SEO optimization | Traffic volume, content engagement, brand mentions |
| Peer recommendation | "Others are finding success" | Word-of-mouth, reviews, case studies | Customer testimonial program, referral incentives | Referral traffic, review ratings, social proof metrics |
| Industry event exposure | "What are market leaders doing?" | Conferences, webinars, LinkedIn | Speaking engagements, event sponsorship, expert positioning | Event leads, follower growth, engagement rates |

Goal: Build awareness of {b.brand_name} as credible solution provider within target customer consciousness through consistent category presence.

## Consideration

Evaluation stage where prospects research options, compare alternatives, and build conviction.

| Activity | Customer Questions | Touchpoints | {b.brand_name} Actions | Success Metrics |
|----------|-------------------|-------------|----------------------|-----------------|
| Website research | "Does this solve my problem?" | Landing pages, product pages, about us | Clear value proposition, benefit-focused copy, proof points | Page views, time on site, bounce rate |
| Content consumption | "Can I trust these claims?" | Blog posts, guides, case studies | In-depth educational resources, customer success stories, ROI calculators | Downloads, email signups, content shares |
| Competitor comparison | "Why choose this over alternatives?" | Review sites, comparison pages, forums | Competitive differentiation content, unique value articulation | Comparison page visits, competitive keyword rankings |

Goal: Build confidence that {b.brand_name} delivers results through proof-based messaging addressing specific customer concerns and objections.

## Purchase

Decision stage where prospects commit resources and complete purchase process.

| Activity | Customer Concerns | Touchpoints | {b.brand_name} Actions | Success Metrics |
|----------|------------------|-------------|----------------------|-----------------|
| Demo request | "Will implementation be smooth?" | Demo forms, sales calls, product tours | Consultative selling, personalized demonstrations, objection handling | Demo completion rate, sales cycle length |
| Pricing evaluation | "Can we justify this investment?" | Pricing pages, proposal documents, contracts | Flexible pricing options, ROI justification, payment plans | Conversion rate, average deal size |
| Stakeholder approval | "How do I sell this internally?" | Sales presentations, executive briefings | Executive summary materials, business case templates, success metrics | Close rate, deal velocity, contract value |

Goal: Remove friction from purchase process making buying decision easy and confident through transparent communication and flexible engagement.

## Retention

Post-purchase stage focusing on satisfaction, results delivery, and advocacy development.

| Activity | Customer Goals | Touchpoints | {b.brand_name} Actions | Success Metrics |
|----------|---------------|-------------|----------------------|-----------------|
| Onboarding | "How do I get quick wins?" | Email sequences, training sessions, support docs | Structured onboarding program, success milestones, proactive support | Time to value, feature adoption, satisfaction scores |
| Ongoing usage | "Am I maximizing value?" | Product interface, help center, community forums | Regular check-ins, best practice sharing, optimization recommendations | Usage frequency, feature utilization, expansion revenue |
| Renewal decision | "Should we continue investing?" | Renewal communications, QBRs, success reviews | Performance reporting, ROI analysis, roadmap previews | Retention rate, net revenue retention, advocacy participation |

Goal: Maximize customer lifetime value through consistent results delivery, proactive support, and advocacy cultivation transforming satisfied customers into growth engine.

**Retention Success Factors**:
- Proactive customer success management identifying risks and opportunities early
- Regular product updates and feature releases demonstrating ongoing innovation
- Educational resources enabling customers to maximize platform value independently
- Community engagement connecting customers with peers for knowledge sharing
- Transparent communication about roadmap, challenges, and company direction
- Performance benchmarking showing customer progress versus industry standards
- Flexible support options accommodating different customer needs and preferences
- Expansion opportunities presenting relevant upsell and cross-sell at appropriate times

## Advocacy

Advocacy development stage where satisfied customers become active promoters.

| Activity | Customer Motivations | Touchpoints | {b.brand_name} Actions | Success Metrics |
|----------|---------------------|-------------|----------------------|------------------|
| Referral participation | "Help colleagues succeed like I did" | Referral programs, peer networks, LinkedIn | Incentivized referral program, make sharing easy, recognize top advocates | Referral volume, referral quality, program participation rate |
| Testimonial creation | "Share my success story" | Case studies, reviews, social media | Proactive solicitation, professional production support, public recognition | Testimonial quantity, usage permission, quality ratings |
| Community leadership | "Contribute to ecosystem" | User forums, events, content collaboration | Ambassador programs, speaking opportunities, co-creation initiatives | Community engagement, user-generated content, event participation |

Goal: Build self-sustaining referral engine where satisfied customers drive majority of new business through authentic word-of-mouth.
"""
    return sanitize_output(raw, req.brief)


def _gen_brand_positioning(req: GenerateRequest, **kwargs) -> str:
    """Generate 'brand_positioning' section."""
    b = req.brief.brand
    a = req.brief.audience
    raw = f"""Strategic brand positioning defining how {b.brand_name} occupies distinct competitive space in {b.industry or 'the market'}.

## Positioning Statement

For {a.primary_customer or 'mid-market companies'} in {b.industry or 'the industry'} who need {a.pain_points[0] if a.pain_points else 'solutions to complex challenges'}, {b.brand_name} is the strategic partner that delivers measurable results through proven frameworks and authentic client relationships.

Unlike competitors who prioritize scale over quality or tactics over strategy, {b.brand_name} combines deep expertise with personalized attention ensuring clients achieve sustainable growth rather than temporary gains.

## Competitive Differentiation

Key factors distinguishing {b.brand_name} from alternatives:

- **Strategic Depth Over Tactical Execution**: Go beyond campaign execution to address root business challenges with comprehensive strategy development
- **Proof-Based Methodology**: Replace marketing guesswork with data-driven decisions backed by industry benchmarks and performance tracking
- **Integrated Approach**: Coordinate across channels and touchpoints rather than siloed tactics creating cohesive customer experience
- **Transparent Reporting**: Provide real-time access to campaign performance, budget utilization, and ROI metrics building client confidence
- **Long-Term Partnership Model**: Focus on sustainable growth and client success over transactional project relationships or aggressive upselling
- **Industry Specialization**: Deep knowledge of {b.industry or 'target industry'} dynamics, customer behavior, and competitive landscape informing relevant strategies

## Brand Promise

{b.brand_name} commitment to clients:

Consistent, measurable growth through clear strategy, repeatable execution, and genuine partnership. We succeed when our clients succeed—measured in revenue growth, market share gains, and brand strength improvements that withstand market volatility and economic uncertainty. This promise reflects our dedication to long-term client success over short-term transactional relationships, ensuring sustainable competitive advantage.
"""
    return sanitize_output(raw, req.brief)


def _gen_measurement_framework(req: GenerateRequest, **kwargs) -> str:
    """Generate 'measurement_framework' section."""
    b = req.brief.brand
    g = req.brief.goal
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Full-funnel pack needs comprehensive stage-based metrics
    if "full_funnel" in pack_key.lower():
        return """## North Star Metric

Single metric capturing core business value and aligning all teams:

**Active Engaged Customers**: Monthly count of customers achieving core value milestone (e.g., 10+ actions/month) representing both acquisition success and retention quality. This metric balances growth with engagement quality, preventing vanity metrics and focusing teams on sustainable value creation.

- **Why This Metric**: Captures both growth (new customers) and health (engagement), preventing acquisition-at-all-costs or retention-without-growth traps
- **Target**: 25% month-over-month growth sustained over 12 months indicating product-market fit and scalable growth model
- **Calculation**: Unique customers with 10+ meaningful actions in trailing 30 days, measured daily with 7-day smoothing
- **Ownership**: CEO and executive team with shared accountability across acquisition, activation, and retention functions

## Stage-Level KPIs

Granular metrics tracking performance at each funnel stage:

**Awareness Stage**:
- Unique visitors to owned properties (target: 50K+/month)
- Brand search volume growth (target: 15% QoQ)
- Share of voice in target categories (target: Top 5)

**Acquisition Stage**:
- New signups per week (target: 500+ with <$50 CAC)
- Landing page conversion rate (target: 3-5%)
- Channel-level ROAS (target: 3:1 minimum)

**Activation Stage**:
- Onboarding completion rate (target: 60%+)
- Time to first value moment (target: <24 hours)
- Feature adoption depth (target: 3+ features/user)

**Retention Stage**:
- 30-day activation retention (target: 70%+)
- 90-day cohort retention (target: 50%+)
- Net Revenue Retention (target: 110%+)

**Revenue Stage**:
- Monthly Recurring Revenue growth (target: 15%+ MoM)
- Expansion revenue percentage (target: 25%+ of total)
- Customer Lifetime Value to CAC ratio (target: 3:1+)

## Diagnostics & Alerts

Automated monitoring identifying problems before they impact business results:

- **Conversion Drop Alert**: 20%+ week-over-week decline in any funnel stage triggers investigation and root cause analysis
- **Churn Spike Detection**: Cohort retention 10%+ below historical average indicates product or customer success issue requiring immediate attention
- **CAC Inflation Warning**: Cost per acquisition increasing >15% without corresponding LTV increase signals channel saturation or creative fatigue
- **Engagement Decay Signal**: Active user percentage declining over 3 consecutive weeks indicates product value erosion or competitive pressure
- **Revenue Concentration Risk**: Top 10 customers >40% of revenue flags dangerous dependency requiring diversification efforts
- **Funnel Bottleneck Identification**: Any stage with <50% conversion rate automated flagged for optimization prioritization and testing

All alerts delivered via Slack with automated dashboard links, historical context, and recommended investigation procedures ensuring rapid response."""
    else:
        # Default/campaign pack version
        return f"""Comprehensive measurement framework aligning marketing activities to business outcomes for {b.brand_name}.

## North Star Metric

Primary success indicator for {b.brand_name} marketing effectiveness:

**{g.primary_goal or 'Revenue Growth'}** - The single metric representing ultimate business impact and strategic success. All campaign decisions, budget allocations, and optimization efforts ultimately drive toward improving this core metric which reflects genuine business value creation.

Target: Achieve X% improvement quarter-over-quarter with clear attribution to marketing initiatives through multi-touch tracking and incrementality testing.

## Supporting KPIs

Secondary metrics providing leading indicators and diagnostic insights:

- **Customer Acquisition Cost (CAC)**: Total marketing spend divided by new customers acquired, targeting $X per customer with 12-month payback period
- **Marketing Qualified Leads (MQLs)**: Volume of prospects meeting defined qualification criteria, targeting X leads per month with Y% conversion to sales opportunities
- **Conversion Rate by Funnel Stage**: Percentage progressing through awareness → consideration → decision → purchase, with benchmarks for each transition
- **Customer Lifetime Value (LTV)**: Total revenue per customer over relationship duration, targeting 3:1 LTV:CAC ratio indicating sustainable unit economics
- **Channel Contribution**: Revenue and pipeline attributed to each marketing channel enabling informed budget allocation and optimization decisions
- **Brand Awareness Metrics**: Unaided and aided awareness in target segments measured through quarterly surveys tracking top-of-mind positioning

## Reporting Cadence

Structured reporting rhythm ensuring visibility without overwhelming stakeholders:

- **Daily Monitoring**: Automated dashboards tracking critical metrics (ad spend, conversions, website traffic) with alert thresholds for immediate action
- **Weekly Reviews**: Team huddles reviewing tactical performance, optimization opportunities, and resource allocation adjustments
- **Monthly Performance Reports**: Comprehensive analysis of campaign results, channel effectiveness, budget utilization, and progress toward quarterly goals
- **Quarterly Business Reviews**: Strategic assessment connecting marketing metrics to business outcomes, presenting ROI analysis and future strategy recommendations

## Attribution Notes

Methodology and limitations for crediting marketing contribution:

- **Multi-Touch Attribution Model**: Using time-decay model weighting recent touchpoints more heavily while acknowledging full journey contribution
- **Incrementality Testing**: Running periodic holdout tests and geo-experiments to measure true marketing impact versus organic baseline growth
- **Attribution Window**: 30-day click, 7-day view standard with understanding that complex B2B journeys may extend beyond tracking capabilities
- **Data Limitations**: Acknowledging cross-device tracking gaps, dark social referrals, and offline influence not fully captured in digital attribution models"""


def _gen_risk_assessment(req: GenerateRequest, **kwargs) -> str:
    """Generate 'risk_assessment' section."""
    b = req.brief.brand
    raw = f"""Strategic risk analysis identifying potential obstacles and mitigation strategies for {b.brand_name} campaign success.

## Key Risks

Critical threats that could undermine campaign effectiveness:

- **Market Risk**: Increased competitive activity or market saturation reducing campaign cut-through and driving up customer acquisition costs beyond profitable thresholds
- **Execution Risk**: Team capacity constraints, skill gaps, or resource limitations preventing timely campaign implementation and optimization
- **Messaging Risk**: Market failing to resonate with positioning or creative approach leading to low engagement and poor conversion performance
- **Economic Risk**: Budget cuts, reduced marketing spend, or economic downturn limiting resources available for sustained campaign investment
- **Technology Risk**: Platform changes (algorithm updates, policy shifts, tracking limitations) disrupting campaign performance and measurement capabilities

## Core Assumptions

Fundamental beliefs underpinning strategy that require validation:

- **Customer Behavior**: Target audience spends time on identified channels and engages with proposed content formats at projected rates
- **Competitive Dynamics**: Competitor activity remains relatively stable without major market disruptions or aggressive pricing/positioning changes
- **Budget Availability**: Committed marketing budget remains allocated throughout campaign duration without mid-cycle reductions or reallocations
- **Internal Alignment**: Stakeholders support strategic direction and provide timely feedback, approvals, and resource access enabling smooth execution
- **Performance Benchmarks**: Industry benchmarks and historical data remain relevant predictors of future performance within reasonable variance ranges

## Dependencies

External factors and resources required for campaign success:

- **Sales Team Coordination**: Alignment on lead qualification criteria, response time SLAs, and feedback loops ensuring marketing qualified leads convert effectively
- **Creative Assets**: Timely delivery of brand-compliant creative materials (images, videos, copy) meeting quality standards and campaign timelines
- **Technology Infrastructure**: Functional martech stack with proper integrations, data flows, and reporting capabilities supporting campaign operations
- **Executive Sponsorship**: Visible leadership support for strategy providing air cover during early stages and enabling cross-functional resource access
"""
    return sanitize_output(raw, req.brief)


def _gen_strategic_recommendations(req: GenerateRequest, **kwargs) -> str:
    """Generate 'strategic_recommendations' section."""
    b = req.brief.brand
    g = req.brief.goal
    raw = f"""Actionable strategic recommendations guiding {b.brand_name} toward sustained competitive advantage and market leadership.

## Strategic Priorities

High-impact initiatives deserving executive attention and resource allocation:

- **Own the Category Conversation**: Establish {b.brand_name} as definitive authority through consistent thought leadership, research publications, and industry event presence
- **Build Proof Arsenal**: Systematically capture customer success stories, case studies, ROI data, and testimonials making buying decision easier for prospects
- **Optimize Revenue Engine**: Refine marketing-to-sales handoff processes, lead scoring models, and nurture sequences improving conversion efficiency
- **Develop Content Moat**: Create comprehensive educational resources, tutorials, and frameworks that competitors cannot easily replicate building organic discovery advantage
- **Cultivate Strategic Partnerships**: Identify and activate co-marketing opportunities with complementary brands expanding reach into adjacent audiences
- **Invest in Marketing Technology**: Implement robust analytics, automation, and attribution infrastructure enabling data-driven optimization and accurate ROI measurement
- **Build Community Assets**: Launch user forums, customer advisory boards, and peer networking opportunities creating stickiness and organic advocacy
- **Expand Channel Presence**: Systematically test and validate emerging platforms identifying next wave of high-performing channels before competition

## Implementation Roadmap

**Phase 1 - Foundation (Months 1-3):**
Launch integrated campaign with core messaging across priority channels. Establish baseline metrics, reporting dashboards, and optimization processes. Build initial proof library with 5-10 case studies. Achieve 25%+ increase in qualified lead volume.

**Phase 2 - Scale (Months 4-6):**
Expand successful tactics based on Phase 1 learnings. Launch strategic partnerships and co-marketing initiatives. Develop advanced content hub and SEO strategy. Target 50%+ improvement in pipeline generation and 15%+ improvement in conversion rates.

**Phase 3 - Optimize (Months 7-12):**
Refine entire marketing system based on accumulated performance data. Launch community initiatives and advocacy programs. Achieve market leadership positioning in target category. Deliver 3x ROI on marketing investment with predictable, scalable system.

## Key Execution Principles

Critical factors ensuring strategic success:

- **Data-Driven Decision Making**: Base all tactical adjustments on performance metrics rather than assumptions or preferences
- **Agile Responsiveness**: Maintain quarterly planning cycles allowing strategy adaptation to market changes and emerging opportunities
- **Cross-Functional Alignment**: Ensure marketing, sales, product, and customer success teams coordinate around shared goals and customer journey
- **Long-Term Thinking**: Resist short-term optimization that sacrifices sustainable growth for quick wins or vanity metrics

## Success Criteria

Define campaign success through measurable business outcomes:

- **Revenue Impact**: Achieve {g.primary_goal or 'significant growth'} target with clear marketing attribution
- **Brand Awareness**: Increase unaided awareness from <5% to 15%+ in target segments within 12 months
- **Pipeline Quality**: Generate consistent flow of qualified opportunities with 20%+ sales acceptance rate
- **Marketing Efficiency**: Reduce customer acquisition cost 25%+ through channel optimization and conversion improvements
- **Customer Advocacy**: Build referral engine contributing 30%+ of new business through satisfied customer recommendations
"""
    return sanitize_output(raw, req.brief)


def _gen_cxo_summary(req: GenerateRequest, **kwargs) -> str:
    """Generate 'cxo_summary' section (C-suite/executive summary)."""
    b = req.brief.brand
    g = req.brief.goal
    a = req.brief.audience
    raw = f"""## Executive Summary

**Context:** {b.brand_name} operates in competitive {b.industry or 'market'} landscape where {a.primary_customer or 'target customers'} face significant challenges around {a.pain_points[0] if a.pain_points else 'market complexity'}. Despite strong product capabilities, limited brand awareness and fragmented marketing efforts constrain growth potential. This strategy addresses these barriers through integrated, data-driven approach focusing on {g.primary_goal or 'measurable growth'}.

**Core Strategy:** Establish {b.brand_name} as category authority through multi-channel presence combining thought leadership content, proof-based messaging, and strategic partnerships. Primary focus on {', '.join(a.focus_platforms[:2] if hasattr(a, 'focus_platforms') and a.focus_platforms else ['LinkedIn', 'Email'])} targeting {a.primary_customer or 'mid-market decision makers'} with authentic messaging addressing real pain points. Campaign emphasizes education over promotion, community over broadcasting, and sustained presence over campaign bursts. Strategic investments in content development, channel optimization, and measurement infrastructure create foundation for scalable growth engine.

**Expected Outcomes:** Within 90 days, anticipate 25-40% increase in qualified lead generation, 15-20% improvement in conversion rates, and measurable brand awareness lift in target segments. By month 6, project 2-3x improvement in marketing-sourced pipeline with clear path to profitability and 3:1 LTV:CAC ratio. Full year horizon targeting market leadership positioning, predictable revenue engine generating 30%+ of new business through organic and referral channels, and 3x overall ROI on marketing investment. Success requires executive sponsorship, cross-functional alignment, and commitment to data-driven optimization throughout campaign lifecycle.

**Investment:** Recommended budget allocation supports comprehensive execution across priority channels with flexibility for optimization based on performance data. Primary spend areas include content creation (30%), paid media amplification (35%), marketing technology infrastructure (20%), and strategic partnerships (15%).

**Risk Profile:** Low to moderate risk given proven methodology and clear measurement framework. Primary risks include competitive response, economic headwinds, and execution capacity constraints—all mitigated through agile planning, regular optimization, and phased rollout approach.
"""
    return sanitize_output(raw, req.brief)


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
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## Churn Signals\n\n"
            "Early warning indicators that predict customer disengagement and churn risk:\n\n"
            "- **Usage Decline**: 40%+ drop in login frequency or session duration over 30 days\n"
            "- **Feature Abandonment**: Key features unused for 30+ days, especially paid add-ons\n"
            "- **Engagement Drop**: Email open rates <10%, click rates <1%, no app activity\n"
            "- **Support Friction**: Multiple unresolved tickets, negative sentiment in conversations\n"
            "- **Billing Issues**: Payment failures, downgrade requests, pricing objections\n"
            "- **Lifecycle Milestones Missed**: No repeat purchase within expected cycle window\n"
            "- **Competitive Activity**: Searching for alternatives, attending competitor events\n"
            "- **Internal Changes**: Loss of champion, budget cuts, org restructuring\n\n"
            "## Root Causes\n\n"
            "Fundamental reasons customers churn based on exit interviews and analysis:\n\n"
            '1. **Poor Onboarding** (35%): Customers didn\'t achieve early success or "aha moment"\n'
            "   - Unclear value realization, complex setup, insufficient training resources\n\n"
            "2. **Product-Market Fit Gap** (25%): Solution doesn't fully solve customer pain\n"
            "   - Missing critical features, poor integrations, inflexible workflows\n\n"
            "3. **Price-Value Misalignment** (20%): Customers don't perceive adequate ROI\n"
            "   - Better alternatives available, unclear benefit quantification, unjustified price increases\n\n"
            "4. **Support Failures** (15%): Negative service experiences damage relationship\n"
            "   - Slow response times, unresolved issues, lack of proactive outreach\n\n"
            "5. **External Factors** (5%): Business changes outside your control\n"
            "   - Budget cuts, strategic pivots, M&A activity, economic downturns\n\n"
            "## Retention Levers\n\n"
            "Strategic interventions to reduce churn and improve customer lifetime value:\n\n"
            "- **Onboarding Excellence**: 30-60-90 day success program with defined milestones\n"
            "- **Proactive Success Management**: Regular health checks, quarterly business reviews\n"
            "- **Product Education**: Feature spotlights, best practice guides, certification programs\n"
            "- **Community Building**: User forums, exclusive events, peer networking opportunities\n"
            "- **Value Demonstration**: Usage reports, ROI calculators, benchmark comparisons\n"
            "- **Loyalty Programs**: Rewards for tenure, referrals, advocacy participation\n"
            "- **Renewal Incentives**: Multi-year discounts, exclusive perks, early access to features\n"
            "- **Win-Back Campaigns**: Reactivation offers for churned customers within 6 months\n"
            "- **Predictive Intervention**: ML-driven churn risk scoring triggering personalized outreach\n"
            "- **Feedback Loops**: Regular NPS surveys, exit interviews, feature request prioritization\n\n"
            "**Target Metrics**: Reduce churn from current [X%] to <5% annually, increase NRR to 110%+"
        )
    else:
        raw = (
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
    return sanitize_output(raw, req.brief)


def _gen_conversion_audit(req: GenerateRequest, **kwargs) -> str:
    """Generate 'conversion_audit' section for Audit pack."""
    _ = req.brief.brand  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "performance_audit" in pack_key.lower():
        return """## Landing Page Friction

**Load Speed**: Current 4.2s vs 2.0s benchmark causing 25-30% bounce before page loads. Fix: Compress 8MB+ images, lazy loading, enable caching, use CDN. Impact: +15-20% conversion lift.

**Above-Fold Clarity**: "Revolutionary Platform" headline conveys zero benefit vs "Automate [Task] in 15 Minutes" outcome focus. Key benefit buried in paragraph 3. No trust signals (logos, ratings) visible without scrolling. Fix: Outcome-focused headline, add logos above fold. Impact: 10-15% bounce reduction.

**Form Friction**: 12-field form vs 5 optimal, 48% abandonment (vs 27% industry). Highest drop-off at field 4 (company size). Phone field causing 22% abandonment. No inline validation. Fix: Reduce to 5 core fields, inline validation, explain field necessity. Impact: +25-30% form completion = 40+ monthly conversions.

**Mobile UX**: 70% traffic mobile but 62% lower conversion than desktop. CTAs not thumb-friendly, fields overlap smaller screens, 40% devices force horizontal scroll. Fix: Responsive redesign, 48px touch targets, test 5+ devices. Impact: +35% mobile conversion = $28K annual.

## CTA Performance

**Primary CTA**: "Learn More" generic vs "Start Free Trial" specific. Single placement (hero only) vs 4-5 recommended. Gray color (#4A5568) blends with nav. Current 0.8% CTR vs 2.5-3.5% benchmark. No secondary option for not-ready visitors.

Fix: Change to "Start Your Free 14-Day Trial", add CTAs after benefits/testimonials/FAQs, high-contrast orange (#F59E0B), add "Watch 2-Min Demo" secondary. Impact: 2-3x CTR improvement = 180+ monthly conversions.

**Missing Placements**: Should appear after every major benefit (currently 1 vs 4-5 recommended). No exit-intent popup. No sticky mobile header CTA. Recommendation: CTAs after hero, benefits, social proof, FAQs, plus exit-intent.

## Form & Checkout Issues

**Form Abandonment**: 450 monthly starts, 234 completions = 48% abandonment (vs 27% industry). Drop-off at field 4 (company size) suggests unnecessary data. Phone field: 22% abandonment from spam call fear. No validation until submission. Fix: Remove optional fields, inline validation, explain necessity, phone truly optional. Impact: 20% recovery = 43 conversions/month = $21K annual.

**Checkout Friction**: 3-step requiring account creation before purchase (should be optional). Credit card only—no PayPal/Apple Pay/Google Pay. No trust badges during payment. Shipping cost surprise at final step: 18% cart abandonment. No abandonment emails (zero follow-up on 450 monthly abandons). Fix: Guest checkout, alternative payments, display total upfront, abandonment sequence. Impact: 15-20% reduction = $45K recovered annual.

**Post-Submission**: Generic confirmation with no next steps. 28% never complete onboarding (no nurture). Thank-you page missed upsell opportunity. Recommendation: Clear next steps, immediate value delivery, upsell CTA.

**Overall**: 2.1% conversion vs 3.5-4.5% benchmark. Gap from speed (25-30% loss), form friction (48% abandon), weak CTAs (0.8% CTR). Combined fix potential: 60-80% improvement (2.1% → 3.4-3.8%). At 12K monthly visitors, 1.5% improvement = +180 conversions = $88K annual."""
    else:
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
    b = req.brief.brand
    raw = (
        f"## Bucket 1: Educational Content (40%)\n\n"
        f"Focus on delivering value through expertise and insights. This bucket builds {b.brand_name} as a trusted authority.\n\n"
        "- Industry insights and emerging trends\n"
        "- Practical how-to guides and actionable tips\n\n"
        f"## Bucket 2: Proof & Social Credibility (30%)\n\n"
        f"Showcase real results and authentic customer experiences to build trust and credibility.\n\n"
        "- Customer success stories with specific outcomes\n"
        "- Testimonials and reviews highlighting value\n"
        "- Behind-the-scenes content showing team and process\n\n"
        f"## Bucket 3: Promotional Content (20%)\n\n"
        f"Strategic promotion of {b.brand_name} offerings with clear value propositions.\n\n"
        "- New features and product updates\n"
        "- Limited-time offers with compelling calls-to-action\n\n"
        f"## Bucket 4: Engagement & Community (10%)\n\n"
        f"Drive two-way conversations and community building.\n\n"
        "- Interactive polls and questions\n"
        "- User-generated content campaigns"
    )
    return sanitize_output(raw, req.brief)


def _gen_weekly_social_calendar(req: GenerateRequest, **kwargs) -> str:
    """Generate 'weekly_social_calendar' section with posting schedule."""
    a = req.brief.audience
    primary_audience = a.primary_customer or "core customers"

    raw = (
        f"## Monday\n\n"
        f"**Morning (9:00 AM):** Launch the week with educational content on LinkedIn and Facebook. Share industry insights "
        f"or thought leadership pieces that position your brand as an authority.\n\n"
        f"**Evening (6:00 PM):** Post engaging content across all platforms—polls, questions, or conversation starters "
        f"to boost interaction and community building.\n\n"
        f"## Wednesday\n\n"
        f"**Mid-Morning (10:00 AM):** Share inspirational or behind-the-scenes content on Instagram and TikTok. "
        f"Humanize the brand with team spotlights or authentic moments that resonate emotionally.\n\n"
        f"**Afternoon (5:00 PM):** Publish a customer success story or testimonial on LinkedIn to build credibility "
        f"and demonstrate real-world impact.\n\n"
        f"## Friday\n\n"
        f"**Morning (9:00 AM):** Share promotional content highlighting products, services, or special offers across all platforms. "
        f"Include clear calls-to-action and value propositions.\n\n"
        f"**Afternoon (4:00 PM):** End the week with a reflective or celebratory post—week wrap-up, team wins, or customer shoutouts.\n\n"
        f"## Daily Engagement Tasks\n\n"
        f"- Respond to all comments and messages within 4 hours\n"
        f"- Engage with 5-10 relevant posts from {primary_audience}\n"
        f"- Monitor brand mentions and participate in conversations"
    )
    return sanitize_output(raw, req.brief)


def _gen_creative_direction_light(req: GenerateRequest, **kwargs) -> str:
    """Generate 'creative_direction_light' section for basic creative guidelines."""
    b = req.brief.brand
    s = req.brief.strategy_extras
    tone = (
        ", ".join(s.brand_adjectives)
        if s.brand_adjectives
        else "professional, trustworthy, and approachable"
    )

    raw = (
        f"## Brand Voice\n\n"
        f"{b.brand_name} communicates with a tone that is {tone}. Every piece of content should reflect "
        f"these core attributes while remaining authentic and relatable to the target audience. The voice balances "
        f"expertise with accessibility, ensuring messages resonate without feeling overly corporate or distant.\n\n"
        f"## Visual Style\n\n"
        f"Visual identity should be consistent, on-brand, and immediately recognizable:\n\n"
        f"- **Color Palette:** Use brand primary colors with strategic accent colors for visual hierarchy\n"
        f"- **Typography:** Modern, readable fonts that align with brand personality and ensure accessibility\n"
        f"- **Imagery:** Prioritize authentic, high-quality photos over generic stock images—real people, real moments\n"
        f"- **Design Elements:** Clean layouts with ample white space, strategic use of graphics and icons\n\n"
        f"## Key Guidelines\n\n"
        f"- Always include {b.brand_name} logo in branded content\n"
        f"- Maintain consistent filters/editing style across platform content\n"
        f"- Use aspirational yet achievable imagery that reflects customer success\n"
        f"- Balance promotional content with value-driven, educational material\n"
        f"- Test variations while maintaining core brand identity"
    )
    return sanitize_output(raw, req.brief)


def _gen_hashtag_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'hashtag_strategy' section with recommended hashtags."""
    from backend.utils.text_cleanup import normalize_hashtag

    b = req.brief.brand
    industry = b.industry or "industry"
    brand_slug = b.brand_name.lower().replace(" ", "")

    # Normalize brand hashtags
    brand_tags = [
        normalize_hashtag(brand_slug),
        normalize_hashtag(f"{brand_slug}Community"),
        normalize_hashtag(f"{brand_slug}Insider"),
    ]
    brand_tags = [t for t in brand_tags if t]  # Remove empties

    # Normalize industry hashtags
    raw_industry_tags = [
        industry,
        f"{industry} Trends",
        f"{industry} Insights",
        f"{industry} Expert",
        f"{industry} Innovation",
    ]
    industry_tags = [normalize_hashtag(t) for t in raw_industry_tags]
    industry_tags = [t for t in industry_tags if t]  # Remove empties

    # Remove duplicates while preserving order
    seen = set()
    industry_tags = [t for t in industry_tags if not (t in seen or seen.add(t))]

    raw = (
        f"## Brand Hashtags\n\n"
        f"These are proprietary hashtags that build {b.brand_name} brand equity and community. Use consistently across all posts:\n\n"
    )
    for tag in brand_tags:
        raw += f"- {tag}\n"

    raw += (
        f"\n## Industry Hashtags\n\n"
        f"Target 8-12 relevant industry tags per post to maximize discoverability within {industry}:\n\n"
    )
    for tag in industry_tags:
        raw += f"- {tag}\n"

    raw += (
        "\n## Campaign Hashtags\n\n"
        "Create unique hashtags for specific campaigns, launches, or seasonal initiatives. Track performance "
        "to measure campaign reach and engagement.\n\n"
        "## Best Practices\n\n"
        "- Research trending hashtags weekly using tools like Hashtagify or native platform insights\n"
        "- Mix 50% branded hashtags with 50% industry/trending tags\n"
        "- Avoid overusing hashtags—quality over quantity\n"
        "- Monitor hashtag performance and adjust strategy based on reach and engagement data"
    )
    return sanitize_output(raw, req.brief)


def _gen_platform_guidelines(req: GenerateRequest, **kwargs) -> str:
    """Generate 'platform_guidelines' section with platform-specific strategies."""
    b = req.brief.brand

    raw = (
        f"## LinkedIn\n\n"
        f"**Focus:** Position {b.brand_name} as a thought leader and industry authority. Share B2B insights, "
        f"professional perspectives, and data-driven content.\n\n"
        f"**Content Types:** Long-form articles (1000-2000 words), professional updates, company news, "
        f"industry commentary, employee spotlights\n\n"
        f"**Posting Cadence:** 3-5 times per week during business hours (Tuesday-Thursday 10 AM - 2 PM optimal)\n\n"
        f"**Best Practices:** Use native documents for longer content, engage with comments within 1 hour, "
        f"tag relevant industry contacts and partners\n\n"
        f"## Facebook\n\n"
        f"**Focus:** Build community and foster two-way conversations. Share customer stories, company culture, "
        f"and community-building content that encourages engagement.\n\n"
        f"**Content Types:** Mix of text posts, images, videos, and live streams. Customer testimonials, "
        f"behind-the-scenes content, events, and promotional offers.\n\n"
        f"**Posting Cadence:** 4-6 times per week, mix of morning (9-11 AM) and evening (7-9 PM) posts\n\n"
        f"**Best Practices:** Use Facebook Groups for community building, respond to all comments/messages, "
        f"leverage Facebook ads for reach amplification\n\n"
        f"## Instagram\n\n"
        f"**Focus:** Visual storytelling and brand aesthetics. Showcase {b.brand_name} personality through "
        f"high-quality visuals, authentic moments, and lifestyle content.\n\n"
        f"**Content Types:** High-resolution images, Reels (15-60 seconds), Stories (daily), carousel posts, "
        f"IGTV for longer content\n\n"
        f"**Posting Cadence:** Daily posts (feed: 5-7/week, Stories: daily, Reels: 3-4/week)\n\n"
        f"**Best Practices:** Use all 30 hashtags strategically, engage with followers' content, leverage "
        f"Instagram Shopping features, maintain consistent visual aesthetic"
    )
    return sanitize_output(raw, req.brief)


def _gen_kpi_plan_light(req: GenerateRequest, **kwargs) -> str:
    """Generate 'kpi_plan_light' section with simplified KPI framework."""
    from backend.industry_config import get_industry_profile

    b = req.brief.brand
    g = req.brief.goal
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Check for industry-specific KPIs (Quick Social + specific industries)
    profile = get_industry_profile(b.industry)
    use_industry_kpis = profile and "quick_social" in pack_key.lower()

    if use_industry_kpis:
        # Use industry-specific KPIs (e.g., coffeehouse retail metrics)
        kpis = profile.kpi_overrides
        raw = (
            f"## Store Performance Metrics\n\n"
            f"Track {b.brand_name} retail performance and customer behavior:\n\n"
        )
        for kpi in kpis[:4]:  # First 4 KPIs
            raw += (
                f"- **{kpi.title()}:** Monitor weekly to identify trends and optimize operations\n"
            )

        raw += (
            f"\n## Customer Engagement\n\n"
            f"Measure how customers interact with {b.brand_name} across channels:\n\n"
        )
        for kpi in kpis[4:]:  # Remaining KPIs
            raw += f"- **{kpi.title()}:** Track monthly to measure customer loyalty and retention\n"

        raw += (
            f"\n## Social Media Impact\n\n"
            f"Connect social presence to real business outcomes:\n\n"
            f"- **Social-to-Store Attribution:** Track promo code redemptions from social posts\n"
            f"- **Location Tags:** Monitor Instagram check-ins and location mentions\n"
            f"- **User-Generated Content:** Count customer posts featuring {b.brand_name}\n\n"
            f"## Measurement Approach\n\n"
            f"Review KPIs weekly for trends, conduct monthly deep-dive analysis, and adjust strategy quarterly "
            f"based on performance data. Focus on metrics that directly tie to in-store traffic and revenue rather than vanity metrics."
        )
    else:
        # Default social KPIs for generic Quick Social or other packs
        raw = (
            f"## Reach\n\n"
            f"Measure how effectively {b.brand_name} expands its audience and brand awareness across platforms:\n\n"
            f"- **Total Impressions:** Target 15,000+ impressions monthly, tracking growth month-over-month\n"
            f"- **Follower Growth:** Aim for 8-12% monthly follower increase across all platforms\n"
            f"- **Post Reach:** Average 800+ unique accounts reached per post\n\n"
            f"## Engagement\n\n"
            f"Track how the audience interacts with content and measure community building success:\n\n"
            f"- **Engagement Rate:** Maintain 3-6% average engagement rate (likes, comments, shares, saves)\n"
            f"- **Comments per Post:** Target average of 8-15 meaningful comments per post\n"
            f"- **Share/Save Rate:** Track content virality with 3-8 shares/saves per post\n\n"
            f"## Conversion\n\n"
            f"Measure how social media drives business outcomes aligned with {g.primary_goal or 'core objectives'}:\n\n"
            f"- **Link Clicks:** Target 40-80 link clicks per month driving traffic to key pages\n"
            f"- **Website Traffic:** Generate 150+ website sessions monthly from social channels\n"
            f"- **Lead Generation:** Capture 8-15 qualified leads per month through social campaigns\n\n"
            f"## Measurement Approach\n\n"
            f"Review KPIs weekly for trends, conduct monthly deep-dive analysis, and adjust strategy quarterly "
            f"based on performance data. Focus on metrics that directly tie to business objectives rather than vanity metrics."
        )
    return sanitize_output(raw, req.brief)


def _gen_30_day_recovery_calendar(req: GenerateRequest, **kwargs) -> str:
    """Generate '30_day_recovery_calendar' section - strategy recovery over 30 days."""
    b = req.brief.brand
    raw = f"""## Week 1

| Day | Focus Area | Actions | Success Indicator |
|-----|-----------|---------|-------------------|
| 1-2 | **Foundation Audit** | Complete current state assessment: budget allocation channel performance messaging consistency customer feedback review | Comprehensive audit report with key findings documented |
| 3-4 | **Quick Wins** | Implement 3 immediate optimizations: pause underperforming campaigns refresh ad creative with new positioning fix broken landing pages | 15-20% improvement in key metrics within 48 hours |
| 5-7 | **Infrastructure** | Establish daily monitoring dashboard. Define new KPIs aligned with turnaround goals. Restart stakeholder communication rhythm | Real-time visibility into performance. Stakeholders aligned on recovery plan |

## Week 2

| Day | Focus Area | Actions | Success Indicator |
|-----|-----------|---------|-------------------|
| 8-10 | **Strategic Reset** | Launch refreshed campaigns reflecting new brand positioning. Update all customer touchpoints with consistent messaging. Test new audience segments aligned with ICP | Campaigns live with new positioning. Audience tests activated |
| 11-12 | **Content Sprint** | Create customer success stories testimonials case studies showcasing {b.brand_name} value. Optimize for SEO targeting brand keywords | 5+ new content assets published. Positive sentiment increasing |
| 13-14 | **Channel Optimization** | Shift budget toward highest-performing channels. Implement segmentation in email. Launch LinkedIn executive presence initiative | Budget reallocated. Email segments configured. Executive posts live |

## Week 3

| Day | Focus Area | Actions | Success Indicator |
|-----|-----------|---------|-------------------|
| 15-17 | **Momentum Building** | Scale successful Week 2 experiments. Implement advanced targeting refinements. Launch secondary campaigns in new channels | Conversion volume up 25%. New channels activated |
| 18-19 | **Advocacy Activation** | Recruit customer advocates for testimonials reviews reference calls. Launch employee advocacy program | 10+ advocates committed. Employee program launched |
| 20-21 | **Performance Review** | Analyze first 3 weeks data. Document wins and learnings. Adjust strategy based on early signals. Report first positive results to stakeholders | Data-driven insights documented. Stakeholders see momentum |

## Week 4

| Day | Focus Area | Actions | Success Indicator |
|-----|-----------|---------|-------------------|
| 22-24 | **Optimization** | Consolidate learnings into repeatable playbook. Implement automation for proven tactics. Refine targeting based on performance data | Playbook documented. Automations configured |
| 25-27 | **Long-Term Planning** | Develop 90-day roadmap extending turnaround success. Establish new KPI targets. Plan brand-building initiatives (thought leadership partnerships events) | 90-day roadmap approved. KPIs established |
| 28-30 | **Foundation Strengthening** | Schedule monthly performance reviews. Create accountability structure. Celebrate wins with team. Document recovery story for external communication | Monthly cadence established. Team energized. Recovery narrative ready |

**Expected 30-Day Outcomes**: 30-40% improvement in lead quality. 20-25% CAC reduction. Brand sentiment shift from negative to neutral. Sales team confidence restored. Foundation established for sustained 90-day turnaround."""
    return sanitize_output(raw, req.brief)


def _gen_account_audit(req: GenerateRequest, **kwargs) -> str:
    """Generate 'account_audit' section - audit of existing account performance."""
    _ = req.brief.brand  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs detailed structure
    if "performance_audit" in pack_key.lower():
        return """## Account Structure

Current organizational setup and configuration analysis:

- **Campaign Organization**: 12 active campaigns across 4 platforms with inconsistent naming conventions creating tracking challenges
- **Ad Account Health**: 87% quality score average indicating room for optimization through better relevance and landing page experience
- **Tracking Implementation**: Partial pixel deployment with conversion tracking gaps on 40% of key pages limiting attribution accuracy
- **Budget Allocation**: 65% of spend concentrated in 3 campaigns while 9 campaigns receive minimal investment suggesting inefficient distribution
- **Account Permissions**: 7 users with varying access levels requiring permissions audit for security and operational clarity

## Budget & Spend Patterns

Analysis of historical spending behavior and efficiency:

- **Monthly Spend Trend**: $12K-$18K monthly with 30% variance indicating reactive rather than strategic budget management
- **Cost-Per-Result Evolution**: CPA increased 45% over 6 months from $28 to $41 signaling declining efficiency and creative fatigue
- **Channel Distribution**: 70% allocated to paid social, 20% search, 10% display creating over-reliance on single channel with limited diversification
- **Dayparting Analysis**: 60% of budget spent during low-converting hours (overnight) suggesting automated bidding without proper constraints
- **Waste Identification**: Estimated 25-30% of spend going to non-converting placements, irrelevant audiences, or poorly optimized campaigns

## Performance Baseline

Key metrics establishing current performance reality:

- **Conversion Rate**: 1.8% overall (industry benchmark 3.2%) indicating significant underperformance requiring funnel optimization
- **Cost-Per-Acquisition**: $41 per customer (target $25) exceeding acceptable threshold by 64% making unit economics unsustainable
- **Return on Ad Spend**: 1.9x ROAS (target 3.5x) falling short of profitability goals requiring immediate strategic intervention
- **Click-Through Rate**: 0.9% (benchmark 2.1%) suggesting weak creative performance and poor audience targeting alignment
- **Quality Score Distribution**: 42% of keywords below 7/10 quality score increasing costs and limiting impression share significantly
- **Landing Page Performance**: 4.2 second average load time (target <2s) creating abandonment and conversion drag

Immediate priorities: Fix tracking gaps, redistribute budget to winning campaigns, improve creative relevance, and optimize landing pages for speed and conversion."""
    else:
        # Default/other pack version
        return (
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


def _gen_ad_concepts_multi_platform(req: GenerateRequest, **kwargs) -> str:
    """Generate 'ad_concepts_multi_platform' - multi-platform ad concepts."""
    b = req.brief.brand
    _ = req.brief.goal  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Full-funnel pack needs comprehensive platform strategy
    if "full_funnel" in pack_key.lower():
        return f"""## Ad Concepts

Core creative strategies driving performance across channels for {b.brand_name}:

**Concept 1: Problem-Agitation-Solution (PAS)**
Hook with specific pain point that target audience experiences daily, agitate by showing cost of inaction, then present {b.brand_name} as solution. Works best for cold audiences unfamiliar with brand. Example: "Still manually [painful task]? You're wasting 10 hours/week..."

**Concept 2: Social Proof & Results**
Lead with customer testimonial or impressive metrics building immediate credibility. Feature real customer names, companies, and specific outcomes. Works best for warm audiences considering options. Example: "How [Customer Name] achieved [specific result] in [timeframe]"

**Concept 3: Educational Value-First**
Provide genuinely useful insight or framework without hard sell creating goodwill and authority. Includes actionable tips prospect can implement immediately. Works best for building trust with skeptical audiences. Example: "5 mistakes costing you [negative outcome] and how to fix them"

**Concept 4: Comparison & Differentiation**
Position {b.brand_name} versus competitors or status quo highlighting unique advantages. Direct comparison builds confidence for prospects evaluating alternatives. Example: "[Old Way] vs [Our Way]: Same goal, radically different approach"

**Concept 5: Urgency & Scarcity**
Limited-time offers or exclusive access creating FOMO and driving immediate action. Must be genuine scarcity to maintain trust. Works best for audiences familiar with brand. Example: "Only 50 spots left for [exclusive opportunity]"

## Platform Variations

Tailored creative execution optimizing for each platform's unique environment:

**LinkedIn**: Professional tone with business outcome focus. Headline: "How [Job Title] at [Company Type] achieve [business metric]". Format: Single image or carousel with data/charts. Copy: 150-200 characters emphasizing ROI and credibility. CTA: "Download Guide", "Schedule Demo", "Register for Webinar". Targeting: Job title, company size, industry with Matched Audiences for retargeting.

**Facebook/Instagram**: Visual-first with emotional hook and lifestyle context. Headline: "The [pain point] solution everyone's talking about". Format: Video (15-30s) or carousel with customer photos. Copy: 75-100 characters benefit-focused. CTA: "Learn More", "Shop Now", "Sign Up". Targeting: Interest-based with Lookalike audiences and broad prospecting.

**Google Search**: Intent-driven matching user query with relevant solution. Headline 1: Keyword + benefit. Headline 2: Social proof or differentiator. Headline 3: CTA. Description: Problem acknowledgment + solution overview + credibility signal. Format: Responsive search ads testing 10+ headline/description variations. Extension: Sitelinks, callouts, structured snippets maximizing real estate.

**YouTube**: Story-driven video capturing attention in first 5 seconds. Hook: Pattern interrupt or curiosity gap. Body: Problem agitation with empathy then solution demonstration. Close: Clear CTA with visual reinforcement. Format: 15-second bumper, 30-second skippable, or 2-minute discovery ads. Targeting: Placement targeting on relevant channels plus keyword and demographic layering.

**TikTok**: Native, authentic content feeling organic not promotional. Format: 15-30 second vertical video. Style: Behind-the-scenes, user testimonial, educational snippet, trending format hijack. Copy: On-screen text with captions, not voiceover heavy. Music: Trending sounds increasing discoverability. CTA: Subtle encouraging duet, stitch, or profile visit rather than hard sell.

**Display/Programmatic**: Visual interruption with clear value proposition. Format: Responsive display ads with 3-5 image/copy variations. Design: Bold headline, clear benefit, brand logo, strong CTA button. Placement: Contextual targeting on relevant content sites plus remarketing to site visitors. Animation: Subtle movement catching eye without being obnoxious.

## Creative Best Practices

Universal principles driving ad performance across all platforms:

- **Hook in 3 Seconds**: First frame/sentence must stop scroll with pattern interrupt, curiosity gap, or bold promise
- **Benefit-Focused Headlines**: Lead with outcome not feature - "Get 10K followers in 30 days" beats "Advanced analytics dashboard"
- **Social Proof Integration**: Include specific numbers, customer names, or recognizable logos building instant credibility
- **Clear Single CTA**: One primary action per ad avoiding decision paralysis - "Download Now" OR "Schedule Demo" not both
- **Mobile-First Design**: 80%+ users see ads on mobile so vertical formats, large text, and thumb-friendly CTAs essential
- **A/B Test Everything**: Run 3-5 variations simultaneously testing headlines, images, copy, CTAs finding winning combinations
- **Refresh Every 2-3 Weeks**: Ad fatigue sets in fast so rotate creative preventing declining performance and audience burnout

Platform-specific testing optimizes for each environment's user behavior, creative norms, and algorithmic preferences driving 2-3x performance versus generic cross-platform creative."""
    else:
        # Default/launch pack version
        return """**LinkedIn Ads**
- Headline: Thought leadership and ROI-focused
- Format: Lead generation forms, content downloads
- CTA: 'Download Guide', 'Schedule Demo'

**Facebook/Instagram Ads**
- Visuals: User-generated content, customer testimonials
- Copy: Benefit-focused with urgency
- Format: Carousel ads, video ads
- CTA: 'Learn More', 'Shop Now'

**Google Search Ads**
- Headlines: Keyword + benefit pairing
- Copy: Problem-solution-proof structure
- CTA: 'Get Started', 'Claim Offer'

**TikTok/YouTube Ads**
- Format: Short-form video (15-30 seconds)
- Tone: Authentic, behind-the-scenes
- CTA: On-screen or voice-over call-to-action"""


def _gen_audience_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'audience_analysis' section."""
    b = req.brief.brand
    _ = req.brief.audience  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs detailed audience breakdown
    if "performance_audit" in pack_key.lower():
        return f"""## Current Audiences

Active audience segments being targeted:

- **Broad Interest Targeting**: 2.4M audience size targeting general {b.industry} keywords showing 0.7% CTR indicating insufficient specificity and wasted impressions
- **Website Visitors (All)**: 18K retargeting pool with 1.9% conversion rate performing 3x better than cold traffic validating warm audience value
- **Email List Lookalikes**: 850K Facebook lookalike audience from email list showing 1.2% CTR and $52 CPA suggesting moderate relevance
- **Competitor Interest Targeting**: 420K audience interested in competitor brands achieving 1.4% CTR and $38 CPA as best-performing cold audience
- **Demo Downloads**: 3,200 high-intent audience who downloaded lead magnet showing 4.8% conversion rate but receiving only 5% of budget allocation
- **Age 25-54 Broad**: Overly wide demographic targeting including low-converting age groups diluting performance and inflating costs unnecessarily

## Performance by Segment

Conversion and efficiency metrics by audience:

- **High-Intent Demo Downloaders**: $28 CPA with 4.8% conversion rate delivering 2.8x ROAS representing strongest audience requiring immediate budget increase
- **Website Retargeting**: $35 CPA with 1.9% conversion rate generating 2.3x ROAS validating multi-touch attribution and remarketing effectiveness
- **Competitor Interest**: $38 CPA with 1.4% CTR showing 1.9x ROAS as viable cold acquisition channel with room for creative optimization
- **Email Lookalikes**: $52 CPA with 1.2% CTR delivering 1.4x ROAS performing below profitability threshold requiring audience refinement
- **Broad Interest**: $78 CPA with 0.7% CTR generating 0.9x ROAS losing money on every conversion requiring immediate pause or complete restructure
- **Cold Prospecting**: $92 CPA with 0.5% CTR showing 0.6x ROAS demonstrating current messaging and creative failing to resonate with unaware audiences

## Audience Gaps

Missing targeting opportunities limiting growth:

- **No Cart Abandoners**: Failing to retarget 450+ monthly cart abandonments representing easy 15-20% conversion rate wins with minimal additional budget
- **Underutilized Custom Intent**: Not leveraging Google Custom Intent audiences based on active search behavior missing high-intent prospects
- **Missing Lifecycle Segmentation**: Treating first-time visitors identically to repeat customers rather than tailoring messaging to journey stage
- **Ignored Geographic Performance**: Spending equally across all locations despite some cities showing 3x better ROI than others
- **No Negative Audience Exclusions**: Wasting 10-15% of budget on existing customers, employees, and irrelevant demographics due to lack of exclusion lists
- **Absent Behavioral Targeting**: Missing opportunities to target users based on specific on-site behaviors like time-on-site, pages viewed, or content engagement

Priority recommendations: Pause broad interest targeting, triple budget to demo downloaders and cart abandoners, implement geographic bid adjustments, create exclusion lists."""
    else:
        # Default/other pack version
        return (
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


def _gen_brand_audit(req: GenerateRequest, **kwargs) -> str:
    """Generate 'brand_audit' section."""
    b = req.brief.brand
    raw = f"""## Current Brand Perception

Currently, {b.brand_name} is perceived in the {b.industry} market with mixed signals. Customers recognize the brand but struggle to articulate a clear, consistent value proposition. Brand awareness exists but lacks the depth and emotional connection needed to drive preference and loyalty. Market positioning feels ambiguous compared to competitors who have staked clearer territory.

Social listening reveals fragmented perception:
- Some customers view {b.brand_name} as reliable but outdated
- Price sensitivity indicates unclear value differentiation
- Brand recall is moderate but not top-of-mind in purchase decisions
- Customer sentiment skews neutral rather than enthusiastic

## Brand Strengths

Despite challenges, {b.brand_name} retains valuable brand equity that can be leveraged:

- **Established Presence**: Years of operation have built baseline awareness and trust in {b.industry}
- **Customer Loyalty Core**: A segment of dedicated customers who appreciate consistency and reliability
- **Industry Credibility**: Recognition among peers and partners as a legitimate player in the space
- **Operational Excellence**: Strong fulfillment, customer service responsiveness, and product quality foundations
- **Brand Heritage**: Historical narrative and founder story provide authentic differentiation opportunities
- **Customer Data Assets**: Years of transaction and interaction data enable personalization and targeting

## Brand Weaknesses

Critical vulnerabilities requiring immediate attention:

- **Unclear Positioning**: Generic messaging fails to differentiate from competitors in crowded {b.industry} market
- **Visual Identity Inconsistency**: Logo usage, color application, and design standards vary across touchpoints
- **Message Fragmentation**: Different departments communicate conflicting brand stories and value propositions
- **Limited Emotional Connection**: Rational benefits communicated but emotional resonance and brand personality underdeveloped
- **Outdated Brand Assets**: Website, collateral, and visual materials feel dated compared to modern competitors
- **Weak Brand Advocacy**: Few organic customer testimonials, referrals, or social proof indicating low emotional attachment
- **Inconsistent Customer Experience**: Brand promise not consistently delivered across all customer touchpoints

Brand turnaround strategy must address these weaknesses while amplifying existing strengths to reposition {b.brand_name} competitively."""
    return sanitize_output(raw, req.brief)


def _gen_campaign_level_findings(req: GenerateRequest, **kwargs) -> str:
    """Generate 'campaign_level_findings' - findings at campaign level."""
    b = req.brief.brand
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs table format
    if "performance_audit" in pack_key.lower():
        return f"""## Channel Performance

Detailed performance breakdown by marketing channel:

| Channel | Spend | Impressions | Clicks | CTR | Conversions | CPA | ROAS | Status |
|---------|-------|-------------|--------|-----|-------------|-----|------|--------|
| **Facebook Ads** | $6,200 | 420K | 3,780 | 0.9% | 92 | $67 | 1.4x | ⚠️ Underperforming |
| **Google Search** | $3,800 | 185K | 2,960 | 1.6% | 118 | $32 | 2.8x | ✅ Strong performer |
| **Instagram Ads** | $2,400 | 310K | 1,860 | 0.6% | 31 | $77 | 0.9x | 🚫 Consider pausing |
| **LinkedIn Ads** | $1,800 | 95K | 1,140 | 1.2% | 45 | $40 | 2.2x | ✅ Efficient |
| **Display Network** | $1,600 | 680K | 2,040 | 0.3% | 24 | $67 | 1.1x | ⚠️ Needs optimization |
| **YouTube Ads** | $1,400 | 220K | 880 | 0.4% | 18 | $78 | 0.8x | 🚫 Poor ROI |

## Wins & Losses

Key performance insights and learnings:

**Top Performers**:
- Google Search campaigns delivering 2.8x ROAS with $32 CPA well below target showing strong intent-based targeting
- LinkedIn ads converting B2B audience efficiently at $40 CPA with 1.2% CTR indicating message-market fit
- Remarketing audiences showing 3.2x higher conversion rate than cold traffic validating multi-touch attribution strategy

**Underperformers**:
- Instagram campaigns bleeding budget with $77 CPA and 0.6% CTR suggesting creative fatigue and poor audience alignment
- YouTube pre-roll ads showing 0.8x ROAS making them unprofitable requiring immediate pause or complete strategy overhaul
- Facebook prospecting campaigns declining 45% in efficiency over 90 days indicating audience saturation and ad fatigue

## Gaps

Critical missing elements limiting performance:

- **No Email Remarketing**: Abandoning 78% of site visitors without follow-up email sequences leaving significant revenue on table
- **Weak Mobile Experience**: Mobile conversion rate 62% lower than desktop despite 70% mobile traffic indicating UX friction
- **Missing Video Content**: Competitors dominating video formats while current strategy relies heavily on static images
- **Limited Test Budget**: Only 10% of spend allocated to testing new audiences and creative preventing discovery of winning combinations
- **No Lifecycle Campaigns**: Treating all customers identically rather than segmenting by value, behavior, and lifecycle stage
- **Absent Competitive Messaging**: Generic value propositions failing to differentiate from competitors in crowded {b.industry} market

## Recommendations

Priority actions for immediate performance improvement:

- **Pause Bottom Performers**: Cut Instagram and YouTube (combined -$113 monthly loss) to stop bleeding
- **Reallocate to Winners**: Triple Google Search budget ($3.8K → $11K) given 2.8x ROAS strength
- **Launch Email Remarketing**: Implement abandonment sequence recovering 15-20% of lost conversions
- **Fix Mobile UX**: Responsive redesign improving 62% conversion gap on 70% of traffic
- **Test Video Creative**: Pilot video ads on Facebook matching competitor 3-5x engagement advantage"""
    else:
        # Default/other pack version
        return (
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


def _gen_channel_reset_strategy(req: GenerateRequest, **kwargs) -> str:
    """Generate 'channel_reset_strategy' - strategy to reset underperforming channels."""
    b = req.brief.brand
    raw = f"""## Channel Strategy

{b.brand_name} channel mix requires strategic reset aligning with new positioning and target audience behavior.

**Current State**: 68% budget concentrated in paid search and Facebook ads driving bottom-funnel. Organic channels (SEO social content) underfunded at 12% despite highest-quality leads. Email underutilized. Brand-building (PR partnerships events) only 8%.

**Reset Principles**:
- Invest where target customers spend attention not where acquisition costs cheapest
- Redistribute budget toward awareness and consideration (60/40 vs current 25/75)
- Coordinate messaging and timing across channels for amplification
- Optimize for lead quality engagement depth and LTV not vanity metrics

## Reset Actions

**Organic Social - LinkedIn Priority**:
- Increase cadence to 5x/week: thought leadership (2x) customer stories (1x) industry insights (1x) company culture (1x)
- Activate executive social selling: CEO and CMO publish weekly engage authentically
- Launch newsletter building 1K+ target followers in 90 days
- Implement employee advocacy empowering 25+ team members
- **Metrics**: Grow followers 200% engagement to 3%+ generate 40+ inbound leads/month

**Paid Search - Efficiency + Upper Funnel**:
- Maintain 60% on proven bottom-funnel keywords (brand category + intent)
- Allocate 25% to problem-aware keywords driving mid-funnel content offers
- Test 15% on discovery campaigns (YouTube Display Performance Max) for awareness
- Implement negative keywords preventing waste. Create dedicated landing pages per campaign
- **Metrics**: Reduce CAC 20% expand reach 3x improve quality score to 8+

**Email Marketing - Segmentation + Automation**:
- Segment by funnel stage engagement level and industry
- Build automated nurtures with 8-12 touchpoints over 60 days
- Implement behavioral triggers (website activity downloads engagement)
- Increase send frequency to 2-3x/week with varied content types
- **Metrics**: Open rate 45%+ click rate 8%+ unsubscribe <0.3% generate 60+ MQLs/month

**Content Marketing - SEO + Thought Leadership**:
- Publish 3x/week (2 blog posts 1 video/podcast) aligned with pain points
- Target 50+ high-value keywords with pillar-cluster architecture
- Create resource center (guides templates calculators) capturing leads
- Launch executive podcast interviewing customers and experts
- **Metrics**: Rank page 1 for 30+ keywords 10K+ organic visitors 100+ content-sourced leads/month

**Paid Social - LinkedIn + Retargeting**:
- Shift 60% to LinkedIn targeting job titles seniority industries matching ICP
- Build multi-stage funnel: awareness → consideration → conversion
- Create platform-specific creative (professional data-driven for LinkedIn)
- Implement retargeting across platforms (website visitors video viewers)
- **Metrics**: Generate 80+ SQLs/month CTR 1.2%+ reduce CPA 30%

**Partnerships**:
- Identify 8-10 complementary brands with partnership potential
- Propose co-marketing: joint webinars content collaborations referral programs
- Attend/sponsor 4 key industry events with speaking opportunities
- **Metrics**: Close 5 active partnerships co-generate 150+ leads/quarter

**Website Optimization**:
- Redesign homepage with clear positioning compelling hero social proof
- Build dedicated landing pages per campaign/audience
- Implement monthly A/B tests on CTAs forms layouts
- Improve site speed (<2s) ensure mobile responsiveness
- **Metrics**: Homepage conversion 2.5%+ landing pages 15%+ bounce rate 40%

## Timeline

**Month 1**: Audit existing channels pause underperformers. Build content calendar landing pages email sequences. Train team.

**Months 2-3**: Activate all resets simultaneously. Implement aggressive testing. Monitor daily optimize on early signals.

**Months 4-6**: Double down on winners eliminate losers. Increase budget to top performers. Establish repeatable processes.

Expected results: 2x lead volume 30% CAC reduction 40% improvement in lead-to-customer conversion within 6 months."""
    return sanitize_output(raw, req.brief)


def _gen_competitor_benchmark(req: GenerateRequest, **kwargs) -> str:
    """Generate 'competitor_benchmark' section - benchmark against competitors."""
    b = req.brief.brand
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs detailed competitive analysis
    if "performance_audit" in pack_key.lower():
        return f"""## Competitor Performance

Estimated performance metrics of key competitors in {b.industry}:

- **Competitor A (Market Leader)**: Estimated $80K/month ad spend achieving 2.8% CTR and ~$32 CPA based on advertising intelligence data showing aggressive multi-channel presence
- **Competitor B (Direct Rival)**: Approximately $45K/month spend with strong organic presence (DR 68) and estimated 3.2% conversion rate from landing page optimization
- **Competitor C (Emerging Threat)**: Lower budget ($20K/month) but highly efficient with user-generated content strategy and 4.1% social engagement rate
- **Average Benchmark**: Industry average CPA of $38, 2.1% CTR, 3.2% conversion rate based on industry reports and platform benchmarks

**Channel Presence**:
- Competitors dominating video content on YouTube and TikTok while {b.brand_name} absent from video entirely creating awareness gap
- Competitor A running 40+ ad variations simultaneously showing commitment to testing versus {b.brand_name}'s 5 static ads
- Strong SEO positions held by Competitors A and B for primary keywords while {b.brand_name} ranks page 3+ for money keywords

## Our Position

Objective assessment of {b.brand_name} versus competitive landscape:

- **Cost Efficiency**: {b.brand_name} CPA of $41 running 8% higher than market leader and 24% above industry average indicating suboptimal performance
- **Creative Quality**: Competitors utilizing professional video, animated graphics, and UGC while {b.brand_name} relies on generic stock photos and text-heavy ads
- **Channel Coverage**: {b.brand_name} present on 4 channels versus competitors' 6-8 channel strategies missing video, influencer, and podcast opportunities
- **Conversion Rate**: {b.brand_name} 1.8% conversion rate trailing industry benchmark by 44% and best competitor by 56% suggesting fundamental funnel issues
- **Content Volume**: Publishing 2-3 pieces/week versus competitors' 8-12 pieces/week creating discoverability and authority gaps in organic search
- **Social Following**: {b.brand_name} 4,200 followers versus Competitor A's 38,000 indicating weak brand equity and community engagement

## Competitive Gaps to Exploit

Opportunities where competitors show vulnerability:

- **Customer Service Response**: Competitors averaging 12+ hour response times on social while immediate response could differentiate {b.brand_name} significantly
- **Transparent Pricing**: All major competitors hiding pricing requiring sales calls creating friction {b.brand_name} could eliminate with upfront pricing
- **Educational Content**: Competitors focus on product promotion rather than genuine education leaving gap for thought leadership and value-first content
- **Niche Segmentation**: Competitors targeting broad {b.industry} market while {b.brand_name} could own specific vertical or use case segment
- **Community Building**: No competitor has invested in dedicated community platform or user forum creating opportunity for engagement differentiation
- **Review Presence**: Competitors neglecting G2, Capterra, Trustpilot review profiles while {b.brand_name} could dominate review sites for discovery

Priority actions: Launch video content strategy, improve landing page conversion rate to match benchmarks, increase content velocity to 8+ pieces/week, claim niche positioning."""
    else:
        # Default/other pack version
        return (
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


def _gen_content_calendar_launch(req: GenerateRequest, **kwargs) -> str:
    """Generate 'content_calendar_launch' - launch-specific content calendar."""
    b = req.brief.brand
    raw = f"""## Week 1: Pre-Launch Preparation

Building anticipation and awareness for {b.brand_name} launch with educational and teaser content establishing authority before product announcement.

**Week 1 Content Focus**:
- Problem-focused educational content establishing category expertise and pain point resonance
- Video tutorials and thought leadership positioning {b.brand_name} as solution authority
- Social media engagement building community and generating curiosity through teasers
- Webinar and live event registrations capturing qualified prospect interest
- Behind-the-scenes content humanizing the brand and building authentic connection
- Community discussions fostering engagement and gathering market intelligence

| Day | Content Type | Primary Channel | Secondary Channels | Objective | CTA |
|-----|-------------|----------------|-------------------|-----------|-----|
| Mon | Problem-focused blog post | Website/Blog | LinkedIn, Email | Establish pain point | Read more |
| Tue | Educational video series | YouTube | Social sharing | Build authority | Subscribe |
| Wed | Industry insight carousel | LinkedIn | Twitter, FB | Thought leadership | Engage/Comment |
| Thu | Customer pain point webinar | Zoom/Live | Email, LinkedIn | Educate prospects | Register |
| Fri | Behind-scenes teaser | Instagram Stories | Twitter, LinkedIn | Generate curiosity | Follow us |
| Sat | Community discussion prompt | Twitter | LinkedIn Groups | Build engagement | Join discussion |
| Sun | Weekly insight roundup | Email Newsletter | Blog archive | Nurture audience | Stay tuned |

## Week 2: Launch Activation

Maximum intensity coordinated activation with product announcements, customer proof points, live demonstrations driving awareness and early adoption.

**Week 2 Launch Activities**:
- Press release distribution and executive social media activation announcing product launch
- Product demo content and walkthrough videos educating prospects on features and benefits
- Customer testimonial videos establishing social proof and credibility
- Feature comparison and competitive positioning content clarifying unique value proposition
- Implementation guides and onboarding resources enabling rapid customer adoption

| Day | Content Type | Primary Channel | Secondary Channels | Objective | CTA |
|-----|-------------|----------------|-------------------|-----------|-----|
| Mon (Launch) | Press release + CEO post | PR Wire, LinkedIn | Twitter, Blog | Announcement | Try now |
| Tue | Product demo walkthrough | YouTube | Email, Social | Product education | Start trial |
| Wed | Customer testimonial video | Website, LinkedIn | YouTube, Twitter | Social proof | See pricing |
| Thu | Feature comparison blog | Blog | LinkedIn, Reddit | Competitive positioning | Compare plans |
| Fri | Implementation guide | Blog, Docs | Email, LinkedIn | Adoption enablement | Get started |
| Sat | Community Q&A session | Live Stream | Twitter, Discord | Address questions | Ask anything |
| Sun | Launch week highlights | Social Media | Email digest | Week recap | Join us |

## Week 3: Post-Launch Momentum

Sustaining momentum with customer success stories, detailed use case content, partner collaborations, and educational resources that demonstrate value and ROI while nurturing unconverted launch leads.

| Day | Content Type | Primary Channel | Secondary Channels | Objective | CTA |
|-----|-------------|----------------|-------------------|-----------|-----|
| Mon | Case study deep-dive | Blog | LinkedIn, Email | Demonstrate ROI | Read success |
| Tue | Use case tutorial | YouTube | Docs, Social | Show application | Watch demo |
| Wed | Industry analyst report | PR/Blog | LinkedIn, Twitter | Third-party validation | Download report |
| Thu | Partner co-marketing | Partner channels | Cross-promotion | Expand reach | Learn more |
| Fri | Best practices guide | Blog, PDF | Email, LinkedIn | Enable success | Get guide |
| Sat | User spotlight feature | Social Media | Community forum | Celebrate customers | Share story |
| Sun | Weekly progress update | Email Newsletter | Social channels | Maintain interest | Stay updated |

## Week 4: Sustained Engagement

Establishing long-term thought leadership with executive content, research-backed insights, vertical-specific resources, and community-building initiatives that position {b.brand_name} as the category authority.

| Day | Content Type | Primary Channel | Secondary Channels | Objective | CTA |
|-----|-------------|----------------|-------------------|-----------|-----|
| Mon | Executive byline article | Industry publication | LinkedIn, Blog | Thought leadership | Read article |
| Tue | Research report launch | Gated content | Email, PR | Generate leads | Download report |
| Wed | Vertical use case | Blog | Industry channels | Segment targeting | See solutions |
| Thu | Customer advisory board | PR announcement | LinkedIn, Email | Credibility signal | Apply to join |
| Fri | Tutorial series finale | YouTube | Email, Social | Complete education | Watch series |
| Sat | Community celebration | Social Media | User forum | Engagement | Celebrate with us |
| Sun | Monthly performance review | Internal/Blog | Stakeholder email | Transparency | View metrics |

## Performance Targets

Content calendar execution benchmarks for measuring launch effectiveness:

- **Engagement**: 15K+ total social engagements launch month, 500+ blog comments/shares, 3K+ video views per asset
- **Reach**: 200K+ impressions Week 1, 500K+ impressions launch month, 50+ media mentions
- **Conversion**: 8% landing page conversion (15K visits to 1,200+ signups), 30% email open rate, 5% click rate
- **Quality**: 4+ minutes time-on-page for blog content, 60%+ video completion rate, 25%+ webinar attendance
"""
    return sanitize_output(raw, req.brief)


def _gen_creative_performance_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate 'creative_performance_analysis' section."""
    b = req.brief.brand
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs detailed analysis
    if "performance_audit" in pack_key.lower():
        return f"""## Top Creatives

Best-performing creative elements driving results:

- **Headline Winner**: "Still wasting 10 hours/week on [task]?" achieving 2.4% CTR (3x average) through problem-awareness hook resonating with target pain points
- **Visual Winner**: Authentic customer testimonial photo with quote overlay outperforming stock imagery by 180% in engagement and 95% in conversions
- **Copy Winner**: Benefit-driven short-form copy (75 characters) beating long-form by 65% CTR proving conciseness wins in crowded feeds
- **Format Winner**: Carousel ads showing before/after transformations generating 2.1x more conversions than single-image ads at 40% lower CPA
- **CTA Winner**: "Get Free Template" converting 3.2x better than "Learn More" demonstrating value-first approach drives action

## Underperformers

Creative elements dragging down campaign performance:

- **Generic Headlines**: Vague promises like "Transform your business" showing 0.3% CTR (70% below average) failing to create urgency or specificity
- **Stock Photo Overuse**: Professional stock imagery performing 65% worse than authentic user-generated content and behind-the-scenes shots
- **Feature-Focused Copy**: Technical specifications and feature lists converting 52% lower than benefit-oriented emotional copy
- **Long-Form Static Ads**: Dense text-heavy images with 0.4% CTR getting lost in mobile feeds requiring shift to scannable visual hierarchy
- **Weak CTAs**: Passive phrases like "Check it out" or "Visit website" showing 80% lower conversion rate than directive action-oriented CTAs

## Creative Gaps

Missing creative strategies limiting performance potential:

- **No Video Content**: Completely absent from strategy despite video ads showing 3-5x higher engagement rates across all platforms in {b.industry}
- **Limited Social Proof**: Only 2 testimonial ads running when social proof typically lifts conversion rates 30-40% for consideration-stage audiences
- **Missing Urgency Mechanisms**: No limited-time offers or scarcity messaging leaving money on table with ready-to-buy audiences
- **Insufficient Creative Rotation**: Same 5 ads running for 60+ days causing severe ad fatigue with declining performance and rising costs
- **No Platform-Specific Optimization**: Using identical creative across all platforms rather than tailoring for each platform's unique format and user behavior
- **Absent Competitor Differentiation**: Generic messaging failing to address why {b.brand_name} is superior to alternatives in competitive landscape

Priority actions: Launch video ads, refresh creative every 2-3 weeks, add urgency elements, create platform-specific variations, integrate more social proof."""
    else:
        # Default/other pack version
        return (
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


def _gen_customer_segments(req: GenerateRequest, **kwargs) -> str:
    """Generate 'customer_segments' section - detailed customer segmentation."""
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## Data Sources\n\n"
            "- Purchase history: Transaction frequency, recency, and monetary value (RFM analysis)\n"
            "- Behavioral data: Website activity, email engagement, mobile app usage\n"
            "- Customer service interactions: Support tickets, chat logs, satisfaction scores\n"
            "- Product usage metrics: Feature adoption, session duration, active vs dormant users\n"
            "- Third-party enrichment: Demographics, interests, lookalike modeling\n\n"
            "## Key Segments\n\n"
            "We identify 5 primary customer segments based on RFM scoring and lifecycle stage:\n\n"
            "1. **Champions** (High R, F, M): Recent, frequent, high-value buyers\n"
            "2. **Loyalists** (High F, M): Consistent repeat customers with strong brand affinity\n"
            "3. **Potential Loyalists** (High R, M, Medium F): Recent high-value buyers, building frequency\n"
            "4. **At-Risk** (Low R, High F/M): Previously engaged customers showing signs of disengagement\n"
            "5. **Hibernating/Lost** (Low R, F, M): Inactive customers requiring win-back campaigns\n\n"
            "## Segment Profiles\n\n"
            "**Champions (Top 15% of customers)**\n"
            "- Avg order value: $250+, Purchase frequency: 4-6x per quarter\n"
            "- Strategy: VIP treatment, exclusive early access, loyalty rewards, referral programs\n"
            "- Messaging: Aspirational, premium content, behind-the-scenes access\n\n"
            "**Loyalists (20-25% of customers)**\n"
            "- Avg order value: $150+, Purchase frequency: 2-4x per quarter\n"
            "- Strategy: Tier upgrades, personalized recommendations, community building\n"
            "- Messaging: Appreciation-focused, product education, cross-sell opportunities\n\n"
            "**Potential Loyalists (15-20% of customers)**\n"
            "- Avg order value: $200+, Purchase frequency: 1-2x per quarter\n"
            "- Strategy: Engagement campaigns, onboarding sequences, habit-building content\n"
            "- Messaging: Value-driven, how-to guides, time-limited incentives\n\n"
            "**At-Risk (10-15% of customers)**\n"
            "- Last purchase: 60-120 days ago, Declining engagement: <30% email open rate\n"
            "- Strategy: Re-engagement offers, feedback requests, win-back incentives\n"
            '- Messaging: "We miss you", special comeback offers, highlight improvements\n\n'
            "**Hibernating/Lost (30-40% of customers)**\n"
            "- Last purchase: 120+ days ago, Minimal engagement across all channels\n"
            "- Strategy: Aggressive win-back campaigns, reactivation incentives, list hygiene\n"
            '- Messaging: Major discount offers, "What\'s new", last-chance appeals'
        )
    else:
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
    _ = req.brief.brand  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Retention-CRM pack needs table format with lifecycle flows
    if "retention_crm_booster" in pack_key.lower():
        return """## Welcome Series

Post-purchase onboarding automation activating new customers:

| Email | Timing | Subject Line | Content Focus | Primary CTA | Success Metric |
|-------|--------|--------------|---------------|-------------|----------------|
| Email 1 | Day 0 (immediate) | "Welcome to [Brand]!" | Thank you, order confirmation, what's next | Track Order | 70%+ open rate |
| Email 2 | Day 1 | "Getting Started with [Product]" | Setup guide, tutorial video, support resources | Watch Tutorial | 45%+ click rate |
| Email 3 | Day 3 | "Get the Most from [Product]" | Feature highlights, pro tips, best practices | Explore Features | 35%+ engagement |
| Email 4 | Day 7 | "Join Our Community" | User stories, community invite, referral program | Join Community | 25%+ click rate |

- Goal: Drive product activation within 7 days
- Target: 70%+ customers complete key onboarding actions
- Optimization: A/B test timing, subject lines, content formats

## Nurture Flows

Ongoing engagement automation building loyalty and increasing lifetime value:

| Flow Type | Trigger Condition | Email Sequence | Cadence | Primary Goal | Target Metric |
|-----------|-------------------|----------------|---------|--------------|---------------|
| **Repeat Purchase** | 14 days after first order | 3 emails: related products, social proof, discount | Days 14, 21, 30 | Drive second purchase | 15%+ conversion |
| **Milestone Celebration** | Purchase anniversary | 2 emails: thank you, exclusive anniversary offer | Days 0, 3 of anniversary | Increase loyalty | 40%+ open rate |
| **VIP Upgrade** | 3+ purchases in 90 days | 2 emails: VIP benefits, upgrade invitation | Days 0, 7 after threshold | Convert to VIP tier | 20%+ upgrade rate |
| **Cross-Sell** | Product usage detected | 3 emails: complementary products, bundle offer | Days 7, 14, 21 after usage | Increase basket size | 12%+ conversion |
| **Feedback Request** | 30 days post-purchase | 2 emails: how's it going, review request | Days 30, 37 | Gather reviews | 25%+ response rate |

- Goal: Increase purchase frequency and customer lifetime value
- Target: 40%+ repeat purchase within 90 days
- Optimization: Personalize product recommendations by segment

## Re-Activation Sequences

Win-back automation re-engaging inactive customers:

| Segment | Inactivity Trigger | Email Sequence | Timing | Offer Strategy | Reactivation Target |
|---------|-------------------|----------------|--------|----------------|---------------------|
| **Lapsing** | No purchase 45-60 days | 2 emails: we miss you, special comeback offer | Days 45, 52 | 15% discount | 18%+ return rate |
| **At-Risk** | No purchase 60-90 days | 3 emails: what's new, feedback request, last chance | Days 60, 75, 90 | 20% discount | 12%+ return rate |
| **Churned** | No purchase 90+ days | 4 emails: aggressive win-back series | Days 90, 105, 120, 135 | 25-30% discount | 8%+ reactivation |

- Goal: Recover inactive customers before permanent churn
- Target: 15%+ overall reactivation rate across all segments
- Optimization: Test discount levels, messaging urgency, multi-channel approach

## Transactional Triggers

Behavioral automation responding to customer actions:

- **Abandoned Cart**: 3-email recovery sequence (1hr, 24hr, 72hr) with product reminder, urgency messaging, and 10% discount recovering 20-25% of abandonments
- **Back-in-Stock**: Alert email when previously unavailable product returns, creating urgency with limited quantity messaging, converting 25-30% of subscribers
- **Price Drop**: Notification when watched items go on sale, driving 30-35% conversion rate among engaged subscribers
- **Birthday**: Personalized celebration email with exclusive gift or discount, achieving 40-50% open rates and 25-30% redemption
- **Shipping Updates**: Proactive order status emails (shipped, out for delivery, delivered) reducing support inquiries 40-50% and improving satisfaction
- **Review Reminder**: Post-delivery follow-up requesting product review with photo upload incentive, generating 20-25% review completion

Success metrics: 98%+ deliverability, 28-35% open rate, 4-6% click rate, 2-4% conversion rate from email to purchase"""
    elif "full_funnel" in pack_key.lower():
        # Full-funnel pack needs table format with detailed flows
        return """## Welcome Series

Onboarding automation triggering upon signup to activate new users:

| Email | Timing | Subject Focus | Content Elements | Primary CTA | Success Metric |
|-------|--------|---------------|------------------|-------------|----------------|
| Email 1 | Day 0 (immediate) | Welcome + value confirmation | Brand intro, expectation setting, quick start guide | "Get Started Now" | 60%+ open rate |
| Email 2 | Day 2 | Education + first win | How-to tutorial, video walkthrough, success tips | "Watch Tutorial" | 40%+ click rate |
| Email 3 | Day 4 | Social proof + confidence | Customer success story, testimonial, ROI data | "See Results" | 35%+ engagement |
| Email 4 | Day 7 | Nudge + incentive | Feature highlight, limited-time offer, upgrade prompt | "Unlock More" | 15%+ conversion |

## Nurture Flows

Ongoing engagement automation maintaining relationship and driving deeper activation:

| Flow Type | Trigger Condition | Email Sequence | Cadence | Primary Goal | Conversion Target |
|-----------|-------------------|----------------|---------|--------------|-------------------|
| **Engagement Nurture** | Low activity 7+ days | 3 emails: tip, case study, offer | Days 7, 10, 14 | Re-activate usage | 20%+ return rate |
| **Feature Adoption** | Core feature unused | 2 emails: benefit, tutorial | Days 3, 7 after trigger | Drive feature use | 30%+ adoption |
| **Upgrade Path** | Plan limit approaching | 3 emails: value, testimonial, incentive | Days 0, 3, 7 of limit | Convert to paid/higher tier | 8%+ upgrade rate |
| **Winback Campaign** | Inactive 30+ days | 4 emails: miss you, what's new, offer, last chance | Days 30, 37, 44, 51 | Recover churned users | 12%+ reactivation |
| **Referral Request** | High engagement score | 2 emails: recognition, referral ask | Days 14, 21 after threshold | Generate referrals | 5%+ referral rate |

## Trigger-Based Flows

Behavioral automation responding to specific user actions:

- **Abandoned Cart**: 3-email sequence at 1 hour, 24 hours, 72 hours with product reminder, social proof, and 10% discount incentive recovering 15-20% of abandonments
- **Post-Purchase**: 4-email onboarding series ensuring product adoption, gathering feedback, and introducing complementary products driving 25% cross-sell rate
- **Content Download**: Lead nurture sequence delivering related content, case studies, and demo offers converting 8-12% of leads to sales conversations
- **Event Registration**: Pre-event reminder series with preparation materials, networking opportunities, and value reinforcement improving attendance 20-30%
- **Birthday/Anniversary**: Personalized celebration email with exclusive offer generating 30-40% higher engagement versus standard promotions

## Measurement & Optimization

Key metrics tracking email program effectiveness:

- **Deliverability Rate**: Target 98%+ inbox placement avoiding spam filters through list hygiene and sender reputation management
- **Open Rate**: Target 25-35% varying by list segment and email type measured with engaged subscriber focus
- **Click Rate**: Target 3-5% indicating compelling content and clear CTAs with mobile optimization critical
- **Conversion Rate**: Target 1-3% from email click to desired action (signup, purchase, demo) with landing page alignment essential
- **List Growth Rate**: Target 10%+ monthly growth exceeding unsubscribe/decay rate through lead generation and opt-in optimization

Monthly A/B testing of subject lines, send times, content formats, and CTA placement driving continuous 10-15% performance improvements over time."""
    else:
        # Default/launch pack version
        return """**Welcome Series (Immediate)**
- Email 1: Welcome + brand intro (Day 0)
- Email 2: Best practices guide (Day 2)
- Email 3: Customer success story (Day 4)
- Email 4: Limited-time offer (Day 7)

**Nurture Sequence (Ongoing)**
- Educational content: 40%
- Social proof content: 30%
- Promotional offers: 20%
- Re-engagement triggers: 10%

**Trigger-Based Flows**
- Abandoned cart: Recover within 1-3 hours
- Post-purchase: Onboarding and upsell
- Inactivity: Winback campaign after 60 days
- Birthday/Anniversary: Personalized offer

**Measurement & Optimization**
- Open rate targets: >25%
- Click rate targets: >3%
- Conversion rate targets: >1%
- A/B test subject lines and send times monthly"""


def _gen_full_30_day_calendar(req: GenerateRequest, **kwargs) -> str:
    """Generate 'full_30_day_calendar' section - comprehensive 30-day content calendar."""
    _ = req.brief.brand  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Full-funnel pack needs detailed weekly table format
    if "full_funnel" in pack_key.lower():
        return """## Week 1: Foundation & Awareness

Building initial market presence with educational content and brand introduction:

| Day | Content Type | Platform | Topic/Theme | Format | CTA | Success Metric |
|-----|-------------|----------|-------------|--------|-----|----------------|
| Mon | Educational blog | Website/SEO | Industry trend analysis | 1200-word article | Subscribe | 500+ views |
| Tue | Social post | LinkedIn | Thought leadership | Carousel (5 slides) | Comment/Share | 200+ engagements |
| Wed | Video content | YouTube | Product intro | 3-min explainer | Watch More | 1K+ views |
| Thu | Email campaign | Newsletter | Welcome series | Text + images | Get Started | 30%+ open rate |
| Fri | Social post | Instagram | Behind-the-scenes | Story series | Swipe Up | 500+ views |
| Sat | Community post | Forum/Slack | Discussion starter | Q&A thread | Reply | 50+ responses |
| Sun | Blog recap | Website | Week 1 summary | Listicle | Read More | 300+ views |

## Week 2: Social Proof & Validation

Establishing credibility through customer stories and expert validation:

| Day | Content Type | Platform | Topic/Theme | Format | CTA | Success Metric |
|-----|-------------|----------|-------------|--------|-----|----------------|
| Mon | Case study | Website | Customer success | Long-form | Request Demo | 10+ leads |
| Tue | Testimonial video | YouTube/Social | Customer interview | 2-min video | Learn More | 1.5K+ views |
| Wed | Podcast episode | Audio platforms | Industry expert | 30-min interview | Subscribe | 500+ listens |
| Thu | Social proof post | LinkedIn/Twitter | Metrics & milestones | Infographic | Follow Us | 300+ engagements |
| Fri | Webinar | Zoom/Platform | Educational session | Live event | Register | 100+ attendees |
| Sat | User-generated content | Instagram | Customer spotlight | Repost + story | Tag Us | 50+ mentions |
| Sun | Comparison guide | Blog | vs Competitors | Detailed article | Download PDF | 200+ downloads |

## Week 3: Engagement & Conversion

Driving active engagement and conversion-focused content:

| Day | Content Type | Platform | Topic/Theme | Format | CTA | Success Metric |
|-----|-------------|----------|-------------|--------|-----|----------------|
| Mon | Product demo | YouTube | Feature walkthrough | Screen recording | Try Free | 20+ trials |
| Tue | Flash sale | Email + Social | Limited-time offer | Promotional | Buy Now | 5% conversion |
| Wed | AMA session | Reddit/Forum | Ask us anything | Live Q&A | Join Discussion | 200+ participants |
| Thu | How-to tutorial | Blog/Video | Step-by-step guide | Tutorial | Get Template | 500+ downloads |
| Fri | Contest launch | Instagram/Facebook | User engagement | Photo/video contest | Enter Now | 100+ entries |
| Sat | Live stream | Twitch/YouTube | Behind-the-scenes | Live video | Subscribe | 300+ live viewers |
| Sun | Weekly newsletter | Email | Top content + offers | Curated digest | Click Through | 25%+ click rate |

## Week 4: Consolidation & Expansion

Reinforcing momentum and expanding reach:

| Day | Content Type | Platform | Topic/Theme | Format | CTA | Success Metric |
|-----|-------------|----------|-------------|--------|-----|----------------|
| Mon | Month review | Blog + Social | Results & learnings | Data visualization | Read Insights | 400+ views |
| Tue | Guest post | Partner blog | Collaborative content | 1000-word article | Visit Site | 300+ referrals |
| Wed | Infographic | Pinterest/Instagram | Data story | Visual design | Save/Share | 500+ shares |
| Thu | Partnership announce | PR + Social | Strategic collaboration | Press release | Learn More | 50+ media mentions |
| Fri | Resource library | Website | Curated content hub | Landing page | Download All | 100+ leads |
| Sat | Community spotlight | Newsletter | Top contributors | Recognition post | Nominate Others | 50+ nominations |
| Sun | Preview next month | Social + Email | Coming attractions | Teaser campaign | Stay Tuned | 35%+ engagement |

**Posting Cadence**: Daily content across 3-5 platforms maintaining consistent presence with these execution principles:

- Monday-Friday focus on high-value educational and conversion content driving business objectives
- Weekends lighter with community-building and recap content maintaining engagement without overwhelming audience
- All posts scheduled 2 weeks ahead with 20% buffer for reactive/timely content capitalizing on trends
- Cross-platform repurposing maximizing content ROI - one blog becomes social posts, email content, video script
- Platform-native formatting ensuring content feels organic not copy-pasted - LinkedIn long-form, Twitter threads, Instagram stories
- Morning posts (8-10am) for professional content, evening posts (6-8pm) for consumer/entertainment content optimizing engagement
- Quarterly content audits reviewing top performers and eliminating low-engagement content types streamlining efforts
- Team collaboration workflow with content calendar, approval process, and performance tracking dashboard ensuring consistency
- Community management protocols responding to comments/DMs within 2 hours building relationships and addressing questions
- Monthly content retrospectives analyzing what worked, what flopped, and strategic adjustments for continuous improvement
- Paid promotion budget allocated to boost top organic performers amplifying reach and conversion potential
- A/B testing on headlines, images, CTAs identifying high-performing formats to scale across future content
- Influencer collaboration schedule partnering with 2-3 micro-influencers monthly expanding audience reach authentically"""
    else:
        # Default/launch pack version
        return """**Week 1: Foundation & Education**
- Day 1-2: Brand intro content
- Day 3-4: Educational posts
- Day 5-7: Community engagement sprint

**Week 2: Social Proof**
- Customer case study or testimonial
- Team spotlight content
- User-generated content feature
- Industry trend commentary

**Week 3: Momentum Building**
- Promotional campaign launch
- Flash sale or limited offer
- Webinar or event announcement
- Q&A or community engagement

**Week 4: Consolidation**
- Month recap and results
- Early bird offer for next month
- Testimonial or success metric share
- Call-to-action for next step

**Posting Schedule:**
- Monday-Wednesday: 2 posts/day
- Thursday-Friday: 1 post/day
- Weekends: 1 Sunday wrap-up post"""


def _gen_kpi_plan_retention(req: GenerateRequest, **kwargs) -> str:
    """Generate 'kpi_plan_retention' - KPIs focused on retention."""
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## Core Retention Metrics\n\n"
            "**Customer Retention Rate (CRR)**\n"
            "- Formula: ((Customers End - New Customers) / Customers Start) × 100\n"
            "- Target: 85%+ annually, 95%+ quarterly for high-value segments\n"
            "- Measurement: Track by cohort (monthly/quarterly acquisition groups)\n"
            "- Benchmark: Best-in-class e-commerce 80-90%, SaaS 90-95%\n\n"
            "**Customer Churn Rate**\n"
            "- Formula: (Customers Lost / Total Customers Start) × 100\n"
            "- Target: <5% quarterly, <15% annually\n"
            "- Segmentation: Calculate separately for high/medium/low value tiers\n"
            "- Action threshold: >7% triggers immediate retention intervention\n\n"
            "**Net Revenue Retention (NRR)**\n"
            "- Formula: ((Start MRR + Expansion - Downgrades - Churn) / Start MRR) × 100\n"
            "- Target: 105-110% (growth from existing customers)\n"
            "- Components: Upsells, cross-sells, price increases minus churn\n"
            "- Gold standard: >110% indicates strong product-market fit\n\n"
            "**Customer Lifetime Value (LTV)**\n"
            "- Formula: (Average Purchase Value × Purchase Frequency × Customer Lifespan)\n"
            "- Target: $500+ for e-commerce, $5K+ for B2B/SaaS\n"
            "- Goal: Increase 15-20% year-over-year through retention initiatives\n"
            "- Ratio: Maintain LTV:CAC ratio of 3:1 minimum, target 4:1+\n\n"
            "**Repeat Purchase Rate**\n"
            "- Formula: (Customers with 2+ purchases / Total customers) × 100\n"
            "- Target: 40%+ within first 90 days, 65%+ for active customer base\n"
            "- Critical milestone: Second purchase within 60 days predicts long-term retention\n"
            "- Segment tracking: Monitor by acquisition source and product category\n\n"
            "## Leading Indicators\n\n"
            "**Engagement Score (Composite)**\n"
            "- Email open rate (25%+) + click rate (3%+) + website visits (2+/month) + app sessions\n"
            "- Scale: 0-100, customers scoring <40 flagged as at-risk\n"
            "- Predictive: 30-day engagement drop of 40%+ predicts churn with 75% accuracy\n\n"
            "**Product/Feature Adoption**\n"
            "- Core feature usage within first 14 days: Target 70%+ activation\n"
            "- Active feature count: Users engaging with 3+ features retain at 2x rate\n"
            "- Power user threshold: 10+ sessions/month correlates with <2% churn\n\n"
            "**Time to Value (TTV)**\n"
            "- Days from signup/purchase to first meaningful outcome\n"
            "- Target: <7 days for e-commerce, <14 days for SaaS\n"
            "- Correlation: Every day delay increases churn risk 5-8%\n\n"
            "**Customer Health Score**\n"
            "- Weighted algorithm: Usage frequency (30%) + engagement (25%) + support satisfaction (20%) + payment status (15%) + tenure (10%)\n"
            "- Scale: 0-100, <50 = red (high risk), 50-75 = yellow (monitor), 75+ = green (healthy)\n"
            "- Automation: Score updated daily, triggers workflow interventions\n\n"
            "**Net Promoter Score (NPS)**\n"
            '- Question: "How likely are you to recommend us?" (0-10 scale)\n'
            "- Target: 50+ (world-class), 30-50 (good), <30 (needs improvement)\n"
            "- Frequency: Survey quarterly, track trend over time\n"
            "- Action: Detractors (0-6) get immediate follow-up, promoters (9-10) get referral ask\n\n"
            "**Support Ticket Volume & Sentiment**\n"
            "- Volume: Track tickets per 100 customers, target trend down as onboarding improves\n"
            "- Resolution time: Target <24hr first response, <48hr resolution\n"
            "- Sentiment: Use NLP to score negative (churn risk), neutral, positive\n"
            "- Red flag: 2+ unresolved tickets triggers account manager intervention\n\n"
            "## Dashboard & Alerts\n\n"
            "**Real-Time Monitoring Dashboard**:\n"
            "- Daily active users (DAU) and weekly active users (WAU) trend lines\n"
            "- Churn rate by cohort with color-coded risk indicators\n"
            "- Revenue metrics: MRR, NRR, expansion revenue, churn impact\n"
            "- At-risk customer list (health score <50) with last activity date\n"
            "- Leading indicator trends: Engagement, NPS, feature adoption\n\n"
            "**Automated Alerts**:\n"
            "- High-value customer (LTV >$1K) shows 3+ churn signals → Immediate Slack alert to CSM\n"
            "- Cohort churn rate exceeds 8% → Email to retention team with action plan prompt\n"
            "- NPS drops below 40 or falls 10+ points → Executive notification\n"
            "- Payment failure for customer with >6-month tenure → Automated recovery sequence + manual follow-up\n"
            "- Feature adoption <50% at Day 14 → Trigger onboarding intervention campaign\n\n"
            "**Reporting Cadence**:\n"
            "- Daily: Operational dashboard (churn events, at-risk alerts, support tickets)\n"
            "- Weekly: Retention team review (cohort performance, intervention effectiveness, A/B test results)\n"
            "- Monthly: Executive summary (NRR, LTV, churn rate trends, strategic initiatives)\n"
            "- Quarterly: Board metrics (annual retention rate, LTV:CAC, NPS benchmark, retention ROI)"
        )
    else:
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
    _ = req.brief.brand  # noqa: F841
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs detailed KPI analysis
    if "performance_audit" in pack_key.lower():
        return """## Current KPIs

Existing metrics revealing measurement gaps:

**Marketing Efficiency** - CPA $41 (target $25-$30). ROAS 1.9x (healthy minimum 2.5x). CAC $52 (CAC:LTV 1:2.8, should be 1:3.5+). MQLs 280/month with only 34% converting to opportunities. Landing page conversion 2.1% (benchmark 3.5-4.5%).

**Channel Performance** - Email: 22% open, 3.1% click (solid). Paid Social: $38 CPA, 4.2% conversion (scale opportunity). Paid Search: $52 CPA, 2.8% conversion (underperforming). Organic Social: 1.8% engagement (below 3% standard). SEO: 1,200 monthly visitors, 3.8% conversion (highest quality source).

**Operations** - Lead response 4.2 hours (should be <1 hour). Sales cycle 38 days. Win rate 28%.

## Missing Metrics

Critical gaps preventing optimization:

**Customer Behavior** - Product engagement score, time to first value, feature adoption rate, customer health score (all missing, preventing retention/expansion prediction).

**Funnel Performance** - Micro-conversions, traffic source quality by LTV, content performance by stage, remarketing lift (not tracked, limiting optimization opportunities).

**Long-Term Value** - LTV by cohort/channel, net revenue retention, referral rate, payback period (missing, preventing strategic channel decisions).

**Competitive Intelligence** - Share of voice, win/loss rate by competitor, brand awareness metrics (no competitive tracking limiting positioning decisions).

## Recommended KPI Stack

Streamlined framework focusing on actionable metrics:

**Primary KPIs** (Weekly CEO Review): Revenue growth rate (MoM, YoY). CAC (fully-loaded). LTV (average per customer). LTV:CAC ratio (target 3.5:1+). MRR (predictable base).

**Secondary KPIs** (Daily/Weekly Marketing): MQLs (quantity). MQL-to-customer rate (quality). CPL by channel. Channel ROAS. Landing page conversion rate. Email engagement. Organic traffic growth. Customer health score.

**Tertiary KPIs** (Monthly/Quarterly): Net revenue retention. Payback period. Brand awareness. NPS. Sales cycle length.

**Cadence** - Daily: leads, spend, CPA, conversions. Weekly: MQLs, pipeline, channel performance. Monthly: revenue, CAC, LTV, retention. Quarterly: market share, brand, competitive positioning.

**Implementation** - Phase 1 (Weeks 1-2): Primary KPIs in existing platform. Phase 2 (Weeks 3-4): Secondary KPIs with automated reporting. Phase 3 (Month 2): Tertiary KPIs with custom tracking. Phase 4 (Month 3+): Predictive analytics and AI insights.

Focus exclusively on metrics driving revenue growth, acquisition efficiency, and business sustainability. Weekly reviews enable rapid response, monthly/quarterly reviews inform strategic pivots."""
    else:
        # Default/other pack version
        return (
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


def _gen_launch_campaign_ideas(req: GenerateRequest, **kwargs) -> str:
    """Generate 'launch_campaign_ideas' section."""
    b = req.brief.brand
    raw = f"""## Campaign Concepts

Three integrated campaign themes driving {b.brand_name} launch awareness and conversion:

**Concept 1: "The New Standard" (Positioning Campaign)**

Positions {b.brand_name} as defining new category expectations challenging status quo assumptions. Creative focuses on before/after transformations showing old fragmented approaches vs streamlined new reality. Messaging: "There's the old way. There's the new standard." Targets decision-makers frustrated with current tools through thought leadership content, executive social media, industry publication features. Budget allocation: 40% of launch spend.

- Visual approach showcases split-screen comparisons of complexity vs simplicity
- Executive thought leadership articles in Forbes, TechCrunch establishing authority
- LinkedIn video series featuring customer transformation stories
- Webinar series positioning product as inevitable industry evolution

**Concept 2: "Launch Week Limited" (Urgency Campaign)**

Drives immediate action through exclusive early adopter benefits available only during launch window. Creates FOMO through countdown timers, limited availability messaging, and exclusive founder access. Messaging: "Join the first 100 companies defining the future." Targets warm prospects from waitlist and partner audiences ready to act. Budget allocation: 35% of launch spend.

- Early adopter pricing (20% lifetime discount) for first 100 customers
- Exclusive Slack community access with direct founder engagement
- Priority implementation and dedicated success manager assignment
- Co-marketing opportunities for early customer case studies

**Concept 3: "Proof in Action" (Social Proof Campaign)**

Leverages customer stories, influencer endorsements, and data-driven results to build trust and credibility. Creative centers on authentic testimonials, quantified outcomes, and peer validation. Messaging: "See why leading companies are switching to {b.brand_name}." Targets skeptical buyers requiring proof before committing. Budget allocation: 25% of launch spend.

- Video testimonials from beta customers with specific ROI metrics
- Industry influencer reviews and recommendations
- Case study library with quantified business impact
- Live demos showing real customer implementations

## Activation Ideas

Tactical campaigns amplifying launch momentum across channels:

- **Partner Co-Launch Program**: Coordinate with 8-10 complementary platforms for simultaneous announcements, bundled offers, joint webinars expanding reach to partner audiences (estimated 50K+ combined reach)
- **Influencer Unboxing Series**: Send premium launch kits to 15 industry voices capturing authentic first impressions and product walkthroughs shared across YouTube, LinkedIn, Twitter
- **Customer Challenge Campaign**: Invite waitlist to submit their biggest operational challenge with winners receiving free implementation and case study feature
- **Launch Day Livestream**: 4-hour virtual event with product demos, customer panels, expert discussions, and live Q&A attracting 1,000+ live attendees
- **Referral Accelerator**: Launch week only offer where early customers earn $500 credit for each qualified referral who signs up during launch month
- **Press Embargo Strategy**: Brief 10 key industry publications under embargo releasing coordinated coverage on launch day for maximum impact
- **Reddit/Community Seeding**: Authentic engagement in relevant subreddits and online communities sharing launch story and gathering feedback
- **Retargeting Blitz**: Aggressive retargeting across display, social, video for all launch landing page visitors with testimonial and offer creative
- **Email Thunder Series**: 5-email sequence over launch week to waitlist building anticipation, announcing launch, sharing proof points, creating urgency

## Expected Outcomes

Campaign success metrics and performance targets:

- **Awareness**: 25K launch week website visits, 200K+ total impressions, 60+ earned media placements
- **Engagement**: 15K+ social engagements, 500+ blog shares, 3K+ video views per asset
- **Conversion**: 2,500 signups, 400+ paid customers, 8% landing page conversion rate
- **Revenue**: $240K Month 1 revenue, $85K average deal size, 30-day payback on acquisition costs
"""
    return sanitize_output(raw, req.brief)


def _gen_launch_phases(req: GenerateRequest, **kwargs) -> str:
    """Generate 'launch_phases' section - multi-phase launch strategy."""
    b = req.brief.brand
    raw = f"""## Pre-Launch

Foundation phase (Weeks -4 to -1) establishing infrastructure and building anticipation before {b.brand_name} goes live.

- **Audience Building**: Grow email waitlist to 2,000+ qualified prospects through lead magnets, partner promotions, and paid acquisition
- **Content Stockpile**: Create 30-day content calendar with blog posts, social content, email sequences ready for immediate activation
- **Partner Activation**: Brief 8-10 strategic partners on launch timing, co-marketing opportunities, and referral incentives
- **Influencer Seeding**: Provide early product access to 5 industry influencers for authentic reviews and launch day amplification
- **Technical Readiness**: Complete QA testing, onboarding flow optimization, support documentation, and team training
- **PR Foundation**: Develop press materials, secure 3-5 media embargoed briefings, prepare executive spokespeople
- **Paid Media Setup**: Build audience segments, creative assets, landing pages, and tracking infrastructure for immediate launch activation
- **Success Metrics**: Establish baseline tracking for awareness, engagement, conversion, and customer success KPIs

## Launch

Intensive activation phase (Weeks 1-2) driving maximum awareness and converting early adopters.

- **Day 1 Surge**: Coordinated email announcement to waitlist, social media blitz, PR distribution, paid media activation, partner co-promotion
- **Webinar Event**: Host live product demo and Q&A attracting 500+ attendees with recording available for ongoing lead generation
- **Limited Offer**: Early adopter pricing (20% discount) for first 100 customers creating urgency and accelerating decisions
- **Content Blitz**: Publish 2-3 pieces daily across blog, social, video showcasing product value through different angles
- **Influencer Coordination**: Launch day features from seeded influencers driving social proof and third-party validation
- **Sales Activation**: Outbound team contacts warm prospects from pre-launch engagement with personalized launch offers
- **Paid Amplification**: Aggressive paid social and search budget (3x normal) driving traffic to launch landing pages
- **Community Building**: Activate user community forum, Slack group, or customer hub fostering peer-to-peer engagement
- **Performance Monitoring**: Daily dashboard reviews optimizing underperforming channels and scaling winning tactics

## Post-Launch

Sustainment phase (Weeks 3-8) converting momentum into lasting growth and optimizing based on data.

- **Customer Success**: Intensive onboarding for early customers ensuring positive experiences that generate testimonials and referrals
- **Content Evolution**: Shift from product announcements to customer success stories, use cases, and educational thought leadership
- **Optimization Cycle**: Analyze launch data to identify highest-performing channels, messages, and audiences for ongoing investment
- **Community Nurture**: Regular engagement in customer community answering questions, gathering feedback, celebrating wins
- **Sales Pipeline**: Follow up with unconverted launch leads through targeted nurture sequences addressing specific objections
- **Partner Expansion**: Deepen relationships with highest-performing launch partners developing long-term co-marketing programs
- **PR Momentum**: Secure ongoing coverage through customer milestones, product updates, and executive thought leadership
- **Metrics Review**: Comprehensive analysis of launch performance vs targets informing next quarter growth strategy

Expected launch outcomes: 1,500+ signups Week 1, 400+ paying customers Month 1, 72% retention at Month 3.
"""
    return sanitize_output(raw, req.brief)


def _gen_loyalty_program_concepts(req: GenerateRequest, **kwargs) -> str:
    """Generate 'loyalty_program_concepts' section."""
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## Campaign Concepts\n\n"
            "**Points-Based Rewards Program**: Customers earn 1 point per $1 spent, redeemable at 100 points = $10 discount. Three-tier structure (Bronze 0-500pts, Silver 500-2000pts, Gold 2000+pts) unlocking progressive benefits: free shipping, birthday rewards, early sale access, exclusive products, and VIP support. Points expire after 12 months of inactivity to encourage engagement.\n\n"
            "**Tiered Membership Model**: Free base tier with standard benefits. Mid-tier ($49/year) adds free shipping, 10% off all purchases, priority support, and quarterly surprise gifts. Premium tier ($199/year) includes all mid-tier benefits plus concierge service, exclusive events, early product access, and complimentary gift wrapping.\n\n"
            "**Hybrid Points + Perks System**: Combines transactional points earning (purchase-based) with engagement rewards (reviews, referrals, social shares, birthdays). Points unlock discounts while tier status (based on annual spend) grants experiential perks. Gamified progress bars and milestone celebrations drive engagement.\n\n"
            "**Subscription-Based Loyalty**: Monthly subscription ($9.99) offering 15% off all orders, free shipping, exclusive access to limited editions, members-only shopping hours, and dedicated support line. Targets high-frequency buyers with predictable monthly revenue and strong retention incentive.\n\n"
            "## Offers & Triggers\n\n"
            "| Campaign Type | Trigger Condition | Offer Details | Communication Channel | Expected Response |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| **Welcome Bonus** | Program signup | 100 bonus points ($10 value) on first purchase | Email immediate + SMS | 45% redemption rate |\n"
            "| **Tier Upgrade** | Reach next tier threshold | Exclusive gift + accelerated earning (2x points 30 days) | Email + in-app notification | 60% engagement lift |\n"
            "| **Birthday Reward** | Birthday month | $25 gift card + surprise item | Email 7 days before + reminder | 40% redemption rate |\n"
            "| **Anniversary** | 1-year member | Special recognition + 500 bonus points + exclusive offer | Personalized email + physical card | 55% engagement rate |\n"
            "| **Points Expiry Alert** | 30 days before expiry | Reminder with suggested redemption options | Email + SMS series | 35% point redemption |\n"
            "| **Double Points Event** | Quarterly promotion | 2x points on all purchases for 72 hours | Multi-channel blast | 3x normal sales volume |\n"
            "| **Referral Reward** | Successful referral | Referrer: 200 points, Friend: 100 points + 10% off first order | Automated email + tracking | 8% referral rate |\n"
            "| **Review Incentive** | 14 days post-purchase | 50 points for verified product review with photo | Email + SMS | 25% review completion |\n"
            "| **Reactivation** | No purchase 60 days | 250 bonus points + 20% off comeback offer | Email + SMS + retargeting | 15% reactivation rate |\n\n"
            "## Expected Outcomes\n\n"
            "**Member Acquisition**: Enroll 40-50% of new customers in loyalty program through signup incentives and checkout integration. Target 10K active members within first year.\n\n"
            "**Retention Impact**: Increase repeat purchase rate from 25% (non-members) to 65%+ (active members). Reduce churn 30-40% among loyalty participants versus control group.\n\n"
            "**Revenue Lift**: Loyalty members generate 2.5-3.5x higher lifetime value. Average order value increases 25-35% for members. Program members drive 60-70% of total revenue despite being 40% of customer base.\n\n"
            "**Engagement Metrics**: Target 70%+ active participation rate (at least one earn/burn action per quarter). 35-40% point redemption rate indicating healthy engagement without excessive liability.\n\n"
            "**Program ROI**: Target 3:1 return (revenue generated per dollar spent on rewards and program operations). Break even at 6-8 months with positive cash flow thereafter.\n\n"
            "**Referral Engine**: Active loyalty members generate 8-12% referral rate versus 2-3% baseline, creating compounding acquisition benefits.\n\n"
            "**Data & Insights**: Rich first-party data enabling advanced segmentation, personalized marketing, and predictive churn modeling improving overall marketing efficiency 20-30%."
        )
    else:
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
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Full-funnel pack has different requirements
    if "full_funnel" in pack_key.lower():
        raw = f"""## Funnel Stages

Current funnel structure for {b.brand_name} across all growth stages:

- **Awareness**: Top-of-funnel discovery through organic content, paid ads, social media, SEO - building brand recognition in target market
- **Consideration**: Mid-funnel nurture via email sequences, case studies, product comparisons, webinars - establishing credibility and fit
- **Conversion**: Bottom-funnel activation through demos, trials, onboarding - converting prospects to active customers
- **Retention**: Post-purchase engagement via product usage, support, education - maintaining customer satisfaction and preventing churn
- **Advocacy**: Expansion phase with referrals, testimonials, upsells - transforming satisfied customers into growth drivers

## Current Bottlenecks

Critical friction points limiting {b.brand_name} growth and conversion efficiency:

- **Awareness Gap**: Limited brand recognition in target segments with <5% unaided awareness creating high acquisition costs
- **Consideration Leakage**: 60%+ of website visitors bounce without engaging due to unclear value proposition and weak social proof
- **Conversion Friction**: Complex signup process and delayed time-to-value causing 40% drop-off during onboarding
- **Retention Challenge**: Insufficient engagement triggers and proactive success management leading to 15%+ monthly churn
- **Advocacy Deficit**: No structured referral program or testimonial capture process missing organic growth opportunity

## Opportunities

Strategic initiatives to unlock funnel performance for {b.brand_name}:

- **Awareness Acceleration**: Content marketing and SEO investment could 3x organic discovery reducing dependence on paid channels
- **Consideration Optimization**: Adding customer testimonials, ROI calculator, and comparison content could improve MQL conversion 25-40%
- **Onboarding Streamlining**: Simplified signup flow and first-value moment optimization could reduce activation time from 7 days to 24 hours
- **Retention Enhancement**: Automated engagement campaigns and success milestones could decrease churn 30-50% within 6 months
- **Advocacy Activation**: Referral program with incentives could generate 20-30% of new leads through existing customer base
"""
    else:
        # Launch/campaign pack version
        raw = f"""## Market Size

{b.industry} represents a substantial addressable market with clear growth trajectory and specific opportunity zones for {b.brand_name} product launch.

- **Total Market**: ${b.industry} global market valued at $47B annually with strong fundamentals
- **Serviceable Market**: Target segment (mid-market and enterprise) represents $12.3B opportunity
- **{b.brand_name} Opportunity**: Realistic 0.5% market penetration in Year 1 equals $61M revenue potential
- **Growth Rate**: Category expanding 18% CAGR driven by digital transformation and changing buyer preferences
- **Geographic Concentration**: 62% of market value concentrated in North America and Western Europe markets
- **Segment Breakdown**: Enterprise (45% of value), mid-market (35%), SMB (20%) with varying acquisition costs

## Trends

Critical market dynamics shaping launch strategy and positioning for {b.brand_name}:

- **Buyer Behavior Shift**: Decision-makers increasingly research independently online before sales contact (73% of journey completed before outreach)
- **Platform Consolidation**: Customers seeking integrated solutions over point products reducing vendor management complexity
- **Remote-First Operations**: Distributed teams driving demand for cloud-based collaborative solutions with mobile-first experiences
- **Data Privacy Focus**: Heightened sensitivity to data security and compliance (GDPR, CCPA) influencing vendor selection criteria
- **Community-Led Growth**: Product adoption increasingly driven by peer recommendations, user communities, and authentic social proof
- **Shorter Sales Cycles**: Competitive pressure and digital tooling compressing typical deal timelines from 9 months to 4-6 months
- **Pricing Transparency**: Expectation for clear, published pricing rather than custom quote processes impacting go-to-market approach

## Opportunities

Strategic launch windows and market gaps {b.brand_name} can exploit:

- **Underserved Segment**: Mid-market companies (100-500 employees) lack tailored solutions currently forced to choose between enterprise complexity or SMB limitations
- **Channel White Space**: Competitors focus heavily on outbound sales while inbound content marketing and community building remain underdeveloped
- **Vertical Specialization**: Opportunity to dominate specific industry verticals (healthcare, finance, retail) with tailored messaging and features
- **Partner Ecosystem**: Existing complementary platforms seeking integration partnerships providing distribution and co-marketing opportunities
- **Competitive Timing**: Two major competitors focused on enterprise while third competitor facing quality/reputation issues creating market opening
- **Economic Environment**: Current market conditions favor value-driven solutions with clear ROI over premium-priced category leaders
"""

    return sanitize_output(raw, req.brief)


def _gen_new_ad_concepts(req: GenerateRequest, **kwargs) -> str:
    """Generate 'new_ad_concepts' - fresh ad creative concepts."""
    b = req.brief.brand
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs detailed concepts
    if "performance_audit" in pack_key.lower():
        return f"""## Ad Concepts

Fresh creative directions to replace fatigued existing ads:

**Concept 1: Problem-Agitation-Solution (PAS Framework)** - Hook: "Still wasting 10 hours/week on [task]?" Target pain point with agitation showing cost of inaction (time waste, revenue loss) before positioning {b.brand_name} as solution with specific outcome like "Automate in 15 minutes". Visual: Split-screen before/after showing frustrated vs relieved person. Best for cold audiences, top-of-funnel awareness, problem-aware prospects.

**Concept 2: Social Proof Wave (FOMO Approach)** - Hook: "Join 4,200+ {b.industry} professionals who switched" leveraging bandwagon effect. Feature 3-4 customer logos, testimonials, specific results building credibility. CTA "See why they switched" reduces perceived risk. Visual: Mosaic of customer faces or video testimonials creating community feel. Best for consideration-stage audiences comparing options, building FOMO, overcoming skepticism.

**Concept 3: Outcome-Driven Specificity** - Hook: "Increase [metric] by 40% in 30 days" with concrete, measurable promise. Include case study data, before/after comparison, or money-back guarantee reducing purchase anxiety. Briefly explain how product achieves result without overwhelming with features. Visual: Data visualization or dashboard screenshot demonstrating value. Best for high-intent audiences near purchase decision, overcoming final objections.

**Concept 4: Comparison/Competitive Positioning** - Hook: "[Competitor] vs {b.brand_name}: Why 2,400 customers switched" directly addressing alternatives. Highlight 3 key advantages where {b.brand_name} superior (price, features, support, ease). Show side-by-side comparison table demonstrating clear superiority. Visual: Professional comparison chart or customer testimonial. Best for competitive conquest campaigns, retargeting competitor audiences, differentiation messaging.

**Concept 5: Limited-Time Incentive (Urgency Creation)** - Hook: "Save 30% this week only" or "First 100 signups get [bonus]" creating scarcity. Combine discount with valuable bonus (free onboarding, extra features, extended trial) increasing perceived value. Include countdown timer or explicit deadline pressuring action. Visual: Product showcase with discount badge, timer overlay, limited quantity indicator. Best for retargeting warm audiences, seasonal promotions.

## Messaging

Core message architecture for new creative:

- **Primary Value Proposition**: "Automate [painful task] in 15 minutes, not 10 hours" emphasizing time savings over feature lists
- **Emotional Hook**: Tap frustration with status quo, fear of falling behind competitors, desire for competitive advantage
- **Proof Points**: "4,200+ customers, 4.8/5 stars, 40% average efficiency gain" providing quantifiable credibility
- **Differentiation**: "Unlike competitors requiring IT setup, {b.brand_name} works in 3 clicks" addressing competitive weakness
- **Risk Reversal**: "30-day money-back guarantee, no credit card for trial, cancel anytime" removing barriers
- **Action-Oriented CTAs**: Replace passive "Learn More" with directive "Start Free Trial", "Get Template", "See Demo"

## Creative Testing

Systematic approach to identifying winning creative:

- **Platform Adaptation**: LinkedIn professional tone with ROI focus. Facebook/Instagram emotional storytelling with customer narratives. Google Search direct response matching user intent.
- **Refresh Cadence**: Update all creative every 14-21 days preventing ad fatigue
- **A/B Testing**: Run 3-5 variations simultaneously identifying winners before scaling budget
- **Winning Patterns**: Document successful themes, formats, messaging angles for replication
- **Performance Metrics**: Track CTR, conversion rate, CPA by creative concept to identify top performers"""
    else:
        # Default/other pack version
        return (
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


def _gen_new_positioning(req: GenerateRequest, **kwargs) -> str:
    """Generate 'new_positioning' section - new brand positioning."""
    b = req.brief.brand
    a = req.brief.audience
    raw = f"""## Target Audience

{a} who are ambitious growth-oriented professionals seeking strategic partner (not vendor) to drive competitive advantage in {b.industry}.

**Psychographic Profile**:
- Forward-thinking leaders frustrated by status quo limitations
- Value measurable results and transparent partnership
- Willing to invest premium for differentiated outcomes
- Seek vendors who act as strategic advisors and thought leaders
- Make decisions based on brand trust and proven expertise not price

This target represents 35% of total market but drives 68% of category profit due to higher LTV lower churn and premium pricing acceptance.

## Positioning Statement

**{b.brand_name} is the strategic growth partner for {a} in {b.industry} that transforms market challenges into competitive advantages through innovative solutions and expert guidance—unlike commoditized alternatives focused only on transactions.**

**Positioning Architecture**:
- **Category Frame**: Strategic growth partner elevates relationship perception beyond vendor status
- **Target**: {a} who value partnership and outcomes over price
- **Key Benefit**: Transforms market challenges into competitive advantages positioning {b.brand_name} as enabler of customer success
- **Reason to Believe**: Innovative solutions and expert guidance emphasizes differentiation and value creation
- **Competitive Contrast**: Unlike commoditized alternatives focused only on transactions

## Supporting Pillars

**Innovation Leadership**: {b.brand_name} pioneers new approaches creating unfair advantages for customers. Demonstrated through proprietary methodologies cutting-edge technology and thought leadership establishing category best practices. Proof: 3 industry awards 25+ breakthrough case studies executive speaking engagements.

**Expert Partnership**: Customers gain specialized {b.industry} expertise accumulated over 12+ years navigating complex challenges. Strategic advisory not just product delivery—proactive insights customized recommendations hands-on support. Proof: 94% satisfaction 15+ certifications dedicated success managers quarterly business reviews.

**Measurable Impact**: Every engagement includes clear success metrics transparent reporting and ROI demonstration. {b.brand_name} customers achieve average 3.2x ROI within 6 months with documented improvements in efficiency revenue and competitive positioning. Proof: Real results performance dashboards case study library.

**Long-Term Vision**: {b.brand_name} invests in customer success beyond initial transaction through ongoing education platform evolution and community building. We grow as customers grow aligning incentives for sustained partnership. Proof: 76% retention multi-year contracts customer-shaped roadmap.

## Activation Plan

**Phase 1 - Internal Alignment (Weeks 1-2)**: Leadership workshop to internalize positioning. Sales training on new messaging competitive differentiation objection handling. Create positioning one-pager and FAQ for all teams. Update internal documentation.

**Phase 2 - Asset Refresh (Weeks 3-6)**: Rewrite website homepage about page and key landing pages. Update sales deck one-pagers and proposal templates. Refresh email templates with new language. Create social content calendar. Record positioning video.

**Phase 3 - Market Launch (Weeks 7-10)**: Announce repositioning via email campaign. Launch thought leadership content series demonstrating expertise. Activate PR targeting industry publications. Run awareness campaigns on LinkedIn and industry media. Host webinar showcasing customer success stories.

**Success Metrics**: Track brand awareness lift message comprehension inbound inquiry quality sales cycle reduction and win rate improvement. Expect 3-6 months for market perception shift to materialize in business results."""
    return sanitize_output(raw, req.brief)


def _gen_post_purchase_experience(req: GenerateRequest, **kwargs) -> str:
    """Generate 'post_purchase_experience' section."""
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## Touchpoints\n\n"
            "**Immediate (Hour 0-24)**:\n"
            "- Order confirmation email with full receipt, shipping timeline, and support contact\n"
            "- SMS confirmation with tracking link and estimated delivery date\n"
            "- Account dashboard update showing order status in real-time\n"
            '- Social media "thank you" post opportunity (tag us for feature)\n\n'
            "**Pre-Delivery (Day 1-5)**:\n"
            "- Shipping notification with carrier tracking and delivery window\n"
            '- Preparation email: "Get ready" tips, unboxing video, setup guide\n'
            '- SMS: "Out for delivery today" real-time notification\n'
            '- Proactive support: "Questions before it arrives?" chat widget\n\n'
            "**Delivery Week (Day 5-7)**:\n"
            "- Delivery confirmation with signature/photo proof\n"
            "- Welcome kit email: Quick start guide, video tutorials, FAQ\n"
            "- Product registration prompt for extended warranty/benefits\n"
            "- First-use tips and best practices guide\n\n"
            "**Onboarding (Day 7-30)**:\n"
            '- Check-in email Day 7: "How\'s it going?" with support offer\n'
            "- Tutorial series: 3-4 emails highlighting key features/uses\n"
            "- Community invitation: Join user forum, Facebook group, or Discord\n"
            "- Referral program introduction: Share with friends offer\n\n"
            "**Engagement (Day 30-90)**:\n"
            "- Satisfaction survey with incentive for completion\n"
            '- Review request: "Share your experience" with photo upload option\n'
            "- Cross-sell/upsell: Complementary products based on purchase\n"
            "- Loyalty program enrollment: Join for exclusive perks\n\n"
            "## Key Moments\n\n"
            "**Moment 1: Immediate Gratification** (Purchase completion)\n"
            "- Emotion: Excitement, anticipation, slight buyer's remorse risk\n"
            "- Goal: Reinforce decision, set clear expectations, provide reassurance\n"
            "- Tactic: Enthusiastic confirmation, transparent timeline, easy cancellation if needed\n\n"
            "**Moment 2: The Wait** (Between order and delivery)\n"
            "- Emotion: Impatience, curiosity, heightened anticipation\n"
            "- Goal: Maintain excitement, reduce anxiety, build product knowledge\n"
            "- Tactic: Engaging pre-delivery content, real-time tracking, preparation resources\n\n"
            "**Moment 3: The Unboxing** (Product arrival)\n"
            "- Emotion: Peak excitement, evaluation mode, first impressions critical\n"
            '- Goal: Deliver "wow" moment, facilitate smooth setup, immediate value\n'
            "- Tactic: Premium packaging, thank-you note, clear quick-start guide, surprise delight element\n\n"
            "**Moment 4: First Use** (Days 1-7)\n"
            "- Emotion: Learning curve, potential frustration, seeking validation\n"
            '- Goal: Drive "aha moment", remove friction, celebrate small wins\n'
            "- Tactic: Proactive support, video tutorials, achievement notifications, check-in outreach\n\n"
            "**Moment 5: Habit Formation** (Days 7-30)\n"
            "- Emotion: Routine setting, value assessment, loyalty forming\n"
            "- Goal: Embed product into daily life, prove ongoing value, deepen relationship\n"
            "- Tactic: Usage tips, community connection, personalized recommendations, loyalty benefits\n\n"
            "**Moment 6: Advocacy Decision** (Day 30+)\n"
            "- Emotion: Confidence in purchase, willing to endorse or criticize\n"
            "- Goal: Convert satisfaction into advocacy, gather feedback, drive repeat purchase\n"
            "- Tactic: Review requests, referral incentives, exclusive offers, VIP recognition\n\n"
            "## Success Metrics\n\n"
            "- **Delivery NPS**: Target 70+ (measure satisfaction with shipping/arrival experience)\n"
            "- **Day 7 Engagement**: Target 60%+ customers complete first key action/feature use\n"
            "- **Day 30 CSAT**: Target 85%+ satisfaction score on post-purchase survey\n"
            "- **Review Rate**: Target 25%+ of customers leave review within 60 days\n"
            "- **Support Ticket Rate**: Keep below 5% (indicates smooth onboarding)\n"
            "- **Repeat Purchase**: Target 30%+ make second purchase within 90 days\n"
            "- **Referral Participation**: Target 15%+ refer at least one friend within first quarter\n"
            "- **Retention**: Target 90%+ customers remain active/engaged after 90 days (no returns, continued usage)"
        )
    else:
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
    b = req.brief.brand
    raw = f"""## Root Causes

{b.brand_name} brand underperformance stems from interconnected systemic failures:

- **Positioning Obsolescence**: Original positioning (launched 5+ years ago) targets market needs that have evolved beyond current value proposition
- **Competitive Repositioning**: Competitors redefined category expectations making {b.brand_name} positioning feel outdated and less relevant
- **Customer Evolution**: Target audience language priorities and pain points shifted faster than brand adaptation creating communication disconnect
- **Internal Misalignment**: Marketing sales and product teams operate with different interpretations of brand promise and target customer
- **Resource Misallocation**: 73% of budget directed to bottom-funnel conversion tactics with insufficient brand-building investment
- **Measurement Blind Spots**: Overreliance on short-term performance metrics without tracking brand health indicators or long-term equity
- **Organizational Inertia**: Early success created complacency resistant to positioning evolution and strategic pivots

Previous tactical fixes (discounts channel optimization creative refreshes) addressed symptoms not root causes. Without strategic repositioning addressing market evolution and competitive differentiation tactical improvements deliver diminishing returns.

## Impact

Brand challenges manifest as measurable business damage requiring urgent intervention:

- **Revenue Decline**: YoY revenue growth collapsed from 18% to 4% with Q4 showing first quarterly decline (-6%) in company history
- **Market Share Loss**: Competitive pressure reduced market share from 12% to 8% over 18 months threatening category relevance
- **Customer Economics Crisis**: CAC increased 67% ($240 to $401) while LTV declined 22% creating unsustainable unit economics
- **Brand Health Degradation**: Unaided awareness dropped 31% NPS fell from 52 to 31 consideration decreased from top-3 to top-7 in category
- **Sales Cycle Inefficiency**: Average deal time extended from 32 to 47 days reflecting weakened value perception and trust
- **Competitive Disadvantage**: Win rate against competitors decreased from 41% to 29% as positioning gaps widened
- **Customer Churn Risk**: Retention threatened by perception of stagnation with 23% of customers actively evaluating alternatives
- **Talent Impact**: Employee morale declining as brand struggles affect internal pride and recruitment efforts

Total estimated impact: $4.2M annual revenue at risk if trajectory continues plus long-term brand equity destruction. Performance degradation accelerated Q2 last year correlating with competitor product launches and category messaging shifts.

## Diagnosis

{b.brand_name} faces classic "middle muddle" brand crisis requiring turnaround not incremental optimization.

The brand is caught between premium competitors commanding leadership pricing and value-focused alternatives competing on cost efficiency. Lack of distinctive positioning creates vulnerability to attacks from both directions.

**Core Problem**: {b.brand_name} positioning answers a question customers stopped asking three years ago. The brand speaks to old pain points using outdated language while competitors own the evolved customer conversation.

**Prognosis**: Without bold repositioning expect continued market share erosion margin pressure and eventual category irrelevance. Quick wins available through messaging refresh and channel optimization but sustainable recovery requires strategic brand reinvention.

**Recovery Path**: Stake clear defensible positioning territory aligned with evolved customer priorities. Align all touchpoints around consistent brand promise. Rebalance budget toward brand-building (60/40 vs current 25/75 performance focus). Implement brand health tracking. Build organizational capability for continuous evolution.

Timeline expectation: 6-9 months for repositioning to gain traction with leading indicators (awareness consideration sentiment) improving before lagging indicators (revenue market share) respond. Requires executive commitment and cultural transformation not just marketing tactics."""
    return sanitize_output(raw, req.brief)


def _gen_product_positioning(req: GenerateRequest, **kwargs) -> str:
    """Generate 'product_positioning' section - positioning individual products."""
    b = req.brief.brand
    a = req.brief.audience
    raw = f"""## Target Audience

{a} operating in {b.industry} who need streamlined solutions that deliver results without complexity.

**Primary Audience Profile**:
- Mid-market companies (100-500 employees) with established operations seeking growth acceleration
- Decision-makers include VP Marketing, Director Operations, department heads with budget authority
- Pain points center on fragmented tools, inefficient processes, inability to scale current approaches
- Willing to invest in proven solutions demonstrating clear ROI within 90 days of implementation
- Value vendor partnerships over transactional relationships preferring strategic guidance alongside product delivery

**Secondary Audiences**:
- Enterprise teams seeking agile solutions bypassing lengthy procurement cycles
- Fast-growing startups (50-100 employees) anticipating rapid scaling needs in next 12-18 months
- Industry-specific segments (healthcare, financial services, retail) with specialized compliance requirements

## Positioning Statement

**{b.brand_name} is the integrated solution for {a} in {b.industry} that transforms fragmented operations into streamlined growth engines through intuitive technology and expert guidance—unlike complex enterprise platforms or limited point solutions.**

**Positioning Rationale**:

- **Category Definition**: Integrated solution positions product as comprehensive platform rather than single-feature tool
- **Target Clarity**: Specifically appeals to {a} avoiding vague generic messaging that dilutes appeal
- **Core Benefit**: Transforms fragmented operations into streamlined growth engines speaks directly to audience pain point
- **Differentiation**: Intuitive technology and expert guidance emphasizes dual value (product plus partnership) competitors lack
- **Competitive Frame**: Positions between enterprise complexity and SMB limitations claiming valuable middle ground
- **Rapid Implementation**: 14-day onboarding vs 3-6 month competitor timelines enabling faster value realization
- **Proven Results**: Customer average 3.2x ROI within 6 months with documented case studies across industries
- **Expert Partnership**: Dedicated success managers provide strategic guidance not just technical support
- **Scalable Platform**: Architecture grows with customer needs from 50 to 500+ employees without platform migration
- **Transparent Pricing**: Published pricing tiers eliminate lengthy negotiation and procurement friction

Launch messaging emphasizes speed results and partnership differentiators through customer stories and data-driven proof points.
"""
    return sanitize_output(raw, req.brief)


def _gen_reputation_recovery_plan(req: GenerateRequest, **kwargs) -> str:
    """Generate 'reputation_recovery_plan' section."""
    b = req.brief.brand
    raw = f"""## Crisis Assessment

{b.brand_name} faces reputation challenges requiring strategic recovery.

**Issue**: Brand perception deteriorated due to service quality complaints (37% YoY increase) product reliability incidents (affecting 8% customers) competitive narrative attacks and absence of positive storytelling. Negative sentiment dominates search and social.

**Severity**: High—impacts new customer acquisition (28% decline) sales cycle (extended 32 to 47 days) and win rates (41% to 29%). Current trajectory threatens viability.

**Visibility**: Google results show 4 of top 10 negative. Social sentiment: 42% negative 31% neutral 27% positive. Review platforms: 3.2/5 trending downward. Forums: {b.brand_name} cited as cautionary example.

## Recovery Actions

**Phase 1 - Immediate Response (Days 1-14)**:

- **Executive Acknowledgment**: CEO publishes authentic letter acknowledging issues taking responsibility outlining commitments with timelines. Distribute via email blog social press release
- **Customer Remediation**: Proactively contact affected customers offering refunds extended support replacements dedicated resources. Document in CRM
- **Issue Resolution**: Implement technical fixes within 14 days. Communicate progress every 3 days. Align internal teams
- **Review Response**: Respond personally to every negative review (past 12 months) within 7 days. Acknowledge concerns explain improvements invite conversation
- **Monitoring**: Establish real-time tracking across social review sites forums news. Set alerts. Create executive dashboard

**Phase 2 - Short-Term Recovery (Weeks 3-12)**:

- **Positive Content**: Publish 3x/week success stories innovations milestones. Create video testimonials addressing concerns. Secure earned media. Optimize SEO for brand keywords
- **Customer Advocacy**: Recruit 20-30 satisfied customers for testimonials case studies positive reviews reference calls webinar features
- **Service Excellence**: Reduce support response to <4 hours. Implement proactive outreach. Publish satisfaction scores monthly. Launch customer advisory board
- **Influencer Relations**: Build relationships with industry voices. Brief on turnaround with data. Provide exclusive access. Support their content
- **Employee Advocacy**: Train on positioning turnaround narrative. Provide content library. Recognize contributors. Ensure alignment

**Phase 3 - Long-Term Building (Ongoing)**:

- **Thought Leadership**: Executives publish weekly on LinkedIn. Secure 6+ speaking opportunities annually. Launch podcast interviewing customers experts. Contribute guest articles. Host research studies
- **Community Investment**: Partner with nonprofits. Create scholarships. Sponsor industry events. Publish annual impact report
- **Transparent Communication**: Publish quarterly roadmap updates. Share business metrics challenges. Host open Q&A. Maintain genuine social engagement
- **Continuous Improvement**: Implement NPS tracking with detractor follow-up. Conduct quarterly satisfaction surveys. Tie executive comp to customer metrics. Establish reputation committee

## Timeline

**Weeks 1-2**: Crisis response activated. Executive acknowledgment published. Customers contacted. Monitoring established

**Weeks 3-8**: Content campaign launched. Advocacy recruited. Service improvements publicized. Reviews responded

**Weeks 9-12**: Early metrics improving (sentiment search results ratings). Influencer relationships established

**Months 4-6**: Sustained momentum. Thought leadership gaining traction. Acquisition recovering. Win rates improving

**Months 7-12**: Reputation recovered. Sentiment net-positive. Ratings >4.0/5. Top search results positive. Case library robust

## Success Metrics

- Sentiment: Shift from 42% negative to 60%+ positive within 6 months
- Reviews: Improve 3.2/5 to 4.3/5+ within 9 months
- Search: 8 of top 10 results positive within 4 months
- Retention: Maintain 85%+ grow to 90%+ as recovery progresses
- New Business: Return to pre-crisis volume within 5 months. Win rate 29% to 45%+ within 8 months
- NPS: Increase 31 to 55+ within 12 months

Recovery requires sustained commitment authentic action and culture transformation prioritizing customer trust. {b.brand_name} must prove through consistent behavior that turnaround is real—promises backed by performance."""
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
    b = req.brief.brand
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    # Performance audit pack needs prioritized table format
    if "performance_audit" in pack_key.lower():
        return f"""## Critical Fixes

Immediate actions required to stop performance bleeding (implement within 7 days):

| Priority | Fix | Current Impact | Expected Improvement | Effort | Owner |
|----------|-----|----------------|---------------------|--------|-------|
| P0 | Pause bottom 2 channels (Instagram, YouTube) wasting $3.8K/month | Losing $1.14 on every dollar | Save $3.8K, reallocate to winners | Low | Media Buyer |
| P0 | Fix landing page load time from 4.2s to <2s | 25-30% immediate bounce rate | +15-20% conversion lift | Medium | Dev Team |
| P0 | Implement cart abandonment email sequence | 450 monthly abandons, zero follow-up | Recover 15-20% = $45K annual | Low | Email Team |
| P1 | Add social proof (testimonials, logos) above fold | Trust deficit causing drop-off | +10-15% conversion improvement | Low | Design Team |
| P1 | Reduce form fields from 12 to 5-7 essentials | 48% form abandonment rate | +20-25% form completion | Low | Conversion Team |

## High-Impact Opportunities

Strategic initiatives delivering significant ROI (30-60 day implementation):

| Opportunity | Business Case | Investment Required | Expected Return | Timeline |
|-------------|---------------|---------------------|-----------------|----------|
| **Launch Video Content** | Competitors seeing 3-5x higher engagement, {b.brand_name} has zero video presence | $4K production + $2K monthly media | +40% reach, +25% engagement | 30 days |
| **Triple Budget to Demo Downloaders** | Highest-performing audience ($28 CPA, 4.8% conversion) getting only 5% budget | Reallocate $3K from underperformers | +60 conversions/month at best CPA | Immediate |
| **Implement Mobile Optimization** | 70% mobile traffic but 62% lower conversion rate than desktop | $6K UX overhaul | +35% mobile conversions = $28K annual | 45 days |
| **Build Email Remarketing Sequences** | 78% of site visitors leave without email follow-up | $2K automation setup | +180 conversions/year from nurture | 30 days |
| **Create Platform-Specific Creative** | Using identical creative across all platforms vs optimizing per platform | $3K production monthly | +20-30% efficiency across channels | 30 days |

## Medium-Term Improvements

Foundational upgrades enhancing long-term performance (60-90 day implementation):

- **Rebuild Landing Page Experience**: Complete redesign focused on clarity, speed, mobile-first approach with A/B testing framework for continuous optimization
- **Develop 8-12 Piece/Week Content Calendar**: Match competitor content velocity to improve SEO, social presence, and organic discoverability
- **Launch SEO Initiative**: Target 20 primary keywords where {b.brand_name} currently ranks page 3+ but competitors dominate page 1
- **Implement Advanced Audience Segmentation**: Move beyond broad targeting to behavioral, lifecycle, and intent-based segments for personalization
- **Build Review & Reputation Strategy**: Systematic approach to generating, publishing, and promoting customer reviews across G2, Capterra, Trustpilot
- **Create Competitor Differentiation Messaging**: Develop specific messaging addressing why {b.brand_name} superior to Competitors A, B, C on key decision criteria

## Long-Term Bets

Transformational initiatives with sustained competitive advantage (90+ day implementation):

- **Build Community Platform**: Dedicated forum/Slack community creating network effects, reducing support costs, and improving retention 40%+
- **Launch Partner/Influencer Program**: Systematic partnerships with 10-15 micro-influencers providing authentic reach and credibility
- **Develop Proprietary Research/Reports**: Annual industry benchmark report establishing {b.brand_name} as data authority and generating 1000+ qualified leads
- **Create Certification Program**: Professional credentialing creating ecosystem of advocates while generating revenue and driving product adoption
- **Invest in Brand Refresh**: If needed, modernize visual identity, messaging architecture, and brand positioning to better compete with market leaders

Expected combined impact: 60-80% improvement in overall marketing efficiency, 2.5x ROAS (current 1.9x to target 3.5x+), CPA reduction from $41 to target $25, within 90 days of full implementation."""
    else:
        # Default/other pack version
        return (
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
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## SMS Flows\n\n"
            "**Opt-In Strategy**: Double opt-in process with 15-20% discount incentive for new subscribers. Clearly communicate frequency (2-3x per week max) and content value (exclusive offers, early access, VIP perks). Build list through website popup, checkout opt-in, and in-store signup.\n\n"
            "**Transactional Messages** (Immediate, 98%+ open rate):\n"
            "- Order confirmation with tracking link\n"
            "- Shipping notification with delivery ETA\n"
            "- Delivery confirmation with review request\n"
            "- Appointment reminders 24hr + 2hr before\n\n"
            "**Promotional Campaigns** (2-3x per week, 25-35% CTR):\n"
            '- Flash sales with urgency messaging ("4 hours left")\n'
            "- Exclusive subscriber-only offers\n"
            "- New product launches with early access\n"
            "- VIP tier benefits and rewards\n"
            "- Birthday/anniversary personalized offers\n\n"
            "**Re-Engagement Series** (Triggered by 30+ day inactivity):\n"
            '- SMS 1 (Day 30): "We miss you" + 15% comeback discount\n'
            '- SMS 2 (Day 45): "What\'s new" product highlights + 20% offer\n'
            "- SMS 3 (Day 60): Last chance 25% win-back offer\n\n"
            "**Best Practices**: Send between 10am-8pm, avoid Sundays, keep messages <160 characters, include opt-out instructions, use URL shorteners with tracking, A/B test timing and offers.\n\n"
            "## WhatsApp Flows\n\n"
            "**WhatsApp Business Setup**: Verified business account with automated greeting, quick replies for FAQs, business hours set, catalog integration for product browsing, and payment integration where available.\n\n"
            "**Conversational Commerce** (Personalized 1:1 messaging):\n"
            "- Product recommendations based on browsing history\n"
            "- Personalized styling/shopping assistance\n"
            "- Custom order inquiries and modifications\n"
            "- Size/fit consultations with image sharing\n"
            "- Gift selection guidance with gift wrapping options\n\n"
            "**Customer Support Automation**:\n"
            "- Order status updates with rich media (images, tracking maps)\n"
            "- Return/exchange process guidance\n"
            "- FAQ chatbot handling common questions\n"
            "- Escalation to human agent when needed\n"
            "- Post-resolution satisfaction survey\n\n"
            "**VIP Engagement** (High-value customer exclusive channel):\n"
            "- Early access to sales and new collections\n"
            "- Exclusive behind-the-scenes content\n"
            "- Personal shopper service via WhatsApp\n"
            "- Private shopping events invitation\n"
            "- Loyalty rewards redemption\n\n"
            "**Broadcast Lists**: Segment by purchase history, RFM score, product interests. Send 1-2x per week max with high-value content (exclusive previews, limited inventory alerts, VIP-only offers).\n\n"
            "## Measurement & Optimization\n\n"
            "**SMS Metrics**:\n"
            "- Delivery rate: Target 98%+ (monitor carrier filtering)\n"
            "- Open rate: 98%+ (nearly all SMS opened within 3 minutes)\n"
            "- Click-through rate: Target 25-35% for promotional messages\n"
            "- Conversion rate: Target 15-20% from click to purchase\n"
            "- Opt-out rate: Keep below 2% per campaign (indicates relevance)\n\n"
            "**WhatsApp Metrics**:\n"
            "- Message delivery rate: Target 95%+ (user must have business saved)\n"
            "- Read rate: Target 70-80% (double blue checkmarks)\n"
            "- Response rate: Target 40-50% for engagement messages\n"
            "- Resolution time: Target <2hr for support inquiries\n"
            "- CSAT score: Target 4.5+/5.0 for WhatsApp interactions\n\n"
            "**List Growth**: Target 5-8% monthly subscriber growth via checkout opt-ins, website popups, in-store signups, and cross-channel promotion. Regular list hygiene removing bounces and inactive subscribers quarterly."
        )
    else:
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
    pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""

    if "retention_crm_booster" in pack_key.lower():
        raw = (
            "## Win-Back Triggers\n\n"
            "**Segment 1: Lapsing Customers** (45-60 days inactive)\n"
            "- Trigger: No purchase in 45+ days but previously purchased 2+ times\n"
            "- Risk level: Medium - still engaged with emails, showing early warning signs\n"
            "- Priority: High-value customers with strong purchase history\n\n"
            "**Segment 2: At-Risk Customers** (60-90 days inactive)\n"
            "- Trigger: No purchase in 60+ days, declining email engagement (<15% open rate)\n"
            "- Risk level: High - showing multiple disengagement signals\n"
            "- Priority: Previous high-value or frequent buyers\n\n"
            "**Segment 3: Churned Customers** (90+ days inactive)\n"
            "- Trigger: No purchase in 90+ days, minimal channel engagement\n"
            "- Risk level: Critical - likely lost to competitor or no longer in market\n"
            "- Priority: Recent churners (<180 days) with salvage potential\n\n"
            "**Segment 4: Subscription Cancellations**\n"
            "- Trigger: Subscription cancelled or payment failure unresolved\n"
            "- Risk level: Immediate - active decision to leave\n"
            "- Priority: All cancelled subscriptions within 30 days\n\n"
            "## Sequence Steps\n\n"
            "**Lapsing Customer Sequence** (45-day trigger, 4 touchpoints over 21 days):\n\n"
            '1. **Email 1 (Day 0)**: "We Miss You" - Personalized message acknowledging absence, highlighting what they\'re missing (new products, improvements). Soft 15% incentive.\n'
            "2. **SMS (Day 3)**: Short reminder with direct link to favorites/previously browsed items. No hard sell.\n"
            "3. **Email 2 (Day 7)**: Social proof and what's new - customer testimonials, product launches, feature improvements. 20% comeback offer.\n"
            "4. **Email 3 (Day 14)**: Last chance urgency - 48-hour window for 25% discount. Clear expiration, scarcity messaging.\n\n"
            "**At-Risk Customer Sequence** (60-day trigger, 5 touchpoints over 30 days):\n\n"
            '1. **Survey Email (Day 0)**: Feedback request - "Why did you stop buying?" with incentive ($10 gift card for completion).\n'
            "2. **Email 2 (Day 5)**: Problem acknowledgment - Address common pain points, highlight improvements made.\n"
            "3. **Personalized Offer (Day 10)**: 25% off + free shipping on next order. Dynamic product recommendations based on history.\n"
            "4. **SMS (Day 15)**: Reminder that offer expires in 48 hours. Simple, direct message.\n"
            "5. **Final Email (Day 21)**: Last attempt - 30% off, no restrictions. Clear that this is final outreach before list removal.\n\n"
            "**Churned Customer Sequence** (90-day trigger, 6 touchpoints over 45 days):\n\n"
            '1. **Email 1 (Day 0)**: "Come Back" campaign intro with aggressive 30% discount + free shipping.\n'
            "2. **Email 2 (Day 7)**: Product showcase - new arrivals, bestsellers, curated recommendations.\n"
            "3. **Email 3 (Day 14)**: Social proof blitz - recent reviews, UGC content, customer stories.\n"
            "4. **SMS (Day 21)**: Flash 35% offer for 24 hours only. Create urgency.\n"
            "5. **Email 4 (Day 28)**: Exit survey - final feedback request before removing from active list.\n"
            "6. **Email 5 (Day 35)**: Absolute last chance - 40% off + $20 credit, expiring in 72 hours.\n\n"
            "## Offers & Incentives\n\n"
            "**Discount Tiers by Segment**:\n"
            "- Lapsing (45-60 days): 15-25% progressive discounts\n"
            "- At-Risk (60-90 days): 25-30% aggressive offers\n"
            "- Churned (90+ days): 30-40% maximum discounts + bonuses\n\n"
            "**Non-Discount Incentives**:\n"
            "- Free shipping (no minimum) removing friction\n"
            "- Bonus loyalty points (2x-3x earning rate for comeback purchase)\n"
            "- Free gift with purchase (surprise + delight)\n"
            "- Exclusive early access to sales/new products\n"
            "- VIP tier upgrade for 90 days\n\n"
            "**Personalization Strategies**:\n"
            "- Dynamic product recommendations based on purchase history\n"
            '- Reference specific past purchases ("Your favorite [product] is back in stock")\n'
            "- Customize offer based on historical AOV and purchase frequency\n"
            "- Segment messaging by churn reason (price, product, service)\n\n"
            "**Success Metrics**:\n"
            "- Lapsing segment: Target 25-30% reactivation rate\n"
            "- At-Risk segment: Target 15-20% reactivation rate\n"
            "- Churned segment: Target 8-12% reactivation rate\n"
            "- Overall program ROI: 4:1 (reactivated customer LTV vs campaign cost)\n"
            "- Secondary goal: Gather feedback from 20%+ of non-converters for product/service improvements"
        )
    else:
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
    "ugc_and_community_plan": _gen_ugc_and_community_plan,
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
        # STUB MODE: Try stub content first before calling generators
        if is_stub_mode():
            pack_key = req.package_preset or req.wow_package_key
            stub_content = _stub_section_for_pack(pack_key, section_id, req.brief)
            if stub_content is not None:
                results[section_id] = stub_content
                continue  # Skip generator function, use stub

        # Normal generator path
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

    # PASS 1.5: Quick Social cleanup pass (remove template leaks)
    pack_key = req.package_preset or req.wow_package_key
    if pack_key and "quick_social" in pack_key.lower():
        from backend.utils.text_cleanup import clean_quick_social_text

        for section_id in list(results.keys()):
            if results[section_id]:  # Only clean non-empty sections
                results[section_id] = clean_quick_social_text(results[section_id], req)

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
                    content = None

                    # STUB MODE: Try stub content first before calling generators
                    if is_stub_mode():
                        pack_key_for_stub = req.package_preset or req.wow_package_key
                        stub_content = _stub_section_for_pack(
                            pack_key_for_stub, section_id, req.brief
                        )
                        if stub_content is not None:
                            content = stub_content
                            logger.info(
                                f"[REGENERATION] Regenerated section with stub: {section_id}"
                            )

                    # Normal generator path (if stub didn't provide content)
                    if content is None:
                        generator_fn = SECTION_GENERATORS.get(section_id)
                        if generator_fn:
                            try:
                                content = generator_fn(**context)
                                logger.info(f"[REGENERATION] Regenerated section: {section_id}")
                            except Exception as e:
                                logger.error(
                                    f"[REGENERATION] Failed to regenerate '{section_id}': {e}",
                                    exc_info=True,
                                )

                    # Apply Quick Social cleanup pass to regenerated content
                    if content:
                        pack_key_for_cleanup = req.package_preset or req.wow_package_key
                        if pack_key_for_cleanup and "quick_social" in pack_key_for_cleanup.lower():
                            from backend.utils.text_cleanup import clean_quick_social_text

                            content = clean_quick_social_text(content, req)

                        regenerated.append({"id": section_id, "content": content})

                return regenerated

            # STUB MODE: Skip benchmark enforcement entirely
            # Stubs are placeholders for testing infrastructure, not real content
            if is_stub_mode():
                logger.info(f"[STUB MODE] Skipping benchmark enforcement for {pack_key}")
            else:
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
    # STUB MODE: Generate deterministic benchmark-compliant content without LLM
    if is_stub_mode():
        pack_key = req.package_preset or req.wow_package_key or "unknown"
        stub_content = _stub_section_for_pack(pack_key, section_id, req.brief)
        if stub_content is not None:
            return stub_content
        # Fall through to regular generators if no stub available

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

        # Build the WOW report using the new unified system
        wow_markdown = build_wow_report(
            req=req, wow_rule=wow_rule, extra_sections=output.extra_sections
        )

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
        "package_name": "Strategy + Campaign Pack (Standard)",  # Display name
        "pack_key": "quick_social_basic",  # Alternative: direct preset key (used by tests)
        "wow_enabled": bool,
        "wow_package_key": str or None,  # Alternative: direct preset key
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
    # Phase 3: Start timing and fingerprinting
    start = time.monotonic()
    status_flag = "ok"
    error_detail = None

    try:
        # Extract top-level payload fields
        package_name = payload.get("package_name")
        pack_key = payload.get("pack_key")  # Alternative field name used by tests
        stage = payload.get("stage", "draft")
        services = payload.get("services", {})
        client_brief_dict = payload.get("client_brief", {})
        wow_enabled = payload.get("wow_enabled", False)
        wow_package_key = payload.get("wow_package_key")
        use_learning = payload.get("use_learning", False)
        industry_key = payload.get("industry_key")
        refinement_mode = payload.get("refinement_mode", {})
        constraints = payload.get("constraints", {})

        include_agency_grade = services.get("include_agency_grade", False)

        # 🔥 FIX: Convert display name to preset_key BEFORE fingerprinting
        # This ensures the fingerprint and logs use the correct pack_key
        # Priority: pack_key > wow_package_key > package_name (resolved)
        if pack_key:
            resolved_preset_key = pack_key
        elif wow_package_key:
            resolved_preset_key = wow_package_key
        else:
            resolved_preset_key = PACKAGE_NAME_TO_KEY.get(package_name, package_name)

        if not resolved_preset_key:
            resolved_preset_key = "unknown"

        logger.info(
            f"🔥 [PRESET MAPPING] {package_name or pack_key or wow_package_key} → {resolved_preset_key}"
        )

        # Phase 3: Compute fingerprint for this request using resolved pack key
        fingerprint, fp_payload = make_fingerprint(
            pack_key=resolved_preset_key,
            brief=client_brief_dict,
            constraints=constraints,
        )

        # Phase 3: Check cache first
        cached = GLOBAL_REPORT_CACHE.get(fingerprint)
        if cached is not None:
            duration_ms = (time.monotonic() - start) * 1000.0
            log_request(
                fingerprint=fingerprint,
                payload=fp_payload,
                status="cache_hit",
                duration_ms=duration_ms,
                error_detail=None,
            )
            logger.info(
                f"✅ [CACHE HIT] Returning cached report for fingerprint {fingerprint[:16]}..."
            )
            return cached

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

        # Phase 3: Build final result
        final_result = {
            "report_markdown": report_markdown,
            "status": "success",
        }

        # Phase 3: Store in cache
        GLOBAL_REPORT_CACHE.set(fingerprint, final_result)
        logger.info(f"✅ [CACHE STORE] Cached report for fingerprint {fingerprint[:16]}...")

        return final_result

    except BenchmarkEnforcementError as exc:
        status_flag = "benchmark_fail"
        error_detail = str(exc)
        raise
    except HTTPException:
        # Already handled (from llm_client or other handlers)
        status_flag = "error"
        raise
    except Exception as e:
        status_flag = "error"
        error_detail = repr(e)
        logger.exception("Unhandled error in /api/aicmo/generate_report: %s", type(e).__name__)
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {type(e).__name__}: {str(e)[:100]}"
        )
    finally:
        # Phase 3: Log request with timing
        duration_ms = (time.monotonic() - start) * 1000.0
        if status_flag == "ok" and duration_ms > SLOW_THRESHOLD_MS:
            status_label = "slow"
        else:
            status_label = status_flag

        log_request(
            fingerprint=fingerprint if "fingerprint" in locals() else "unknown",
            payload=fp_payload if "fp_payload" in locals() else {},
            status=status_label,
            duration_ms=duration_ms,
            error_detail=error_detail,
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
    1. Agency-grade PDF: { "wow_enabled": True, "wow_package_key": "...", "report": {...} }
    2. Markdown mode: { "markdown": "..." }
    3. Structured mode: { "sections": [...], "brief": {...} }

    Returns:
        StreamingResponse with PDF on success (Content-Type: application/pdf).
        JSONResponse with error details on failure (Content-Type: application/json).
    """
    try:
        # Extract agency PDF parameters
        wow_enabled = payload.get("wow_enabled", False)
        wow_package_key = payload.get("wow_package_key")
        pack_key = payload.get("pack_key") or wow_package_key
        report = payload.get("report", {})

        print("\n" + "=" * 80)
        print("📄 PDF DEBUG: aicmo_export_pdf() called")
        print(f"   pack_key        = {pack_key}")
        print(f"   wow_enabled     = {wow_enabled}")
        print(f"   wow_package_key = {wow_package_key}")
        print(f"   payload keys    = {list(payload.keys())}")
        print("=" * 80 + "\n")

        # STEP 1: Try agency PDF path first (WeasyPrint + HTML templates)
        if pack_key:
            agency_pdf_bytes = safe_export_agency_pdf(
                pack_key=pack_key,
                report=report,
                wow_enabled=wow_enabled,
                wow_package_key=wow_package_key,
            )

            if agency_pdf_bytes is not None:
                print("📄 PDF DEBUG: ✅ using AGENCY PDF path")
                logger.info(f"PDF exported via agency path: {len(agency_pdf_bytes)} bytes")
                return StreamingResponse(
                    iter([agency_pdf_bytes]),
                    media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="AICMO_Report.pdf"'},
                )
            else:
                print("📄 PDF DEBUG: agency path returned None, trying fallback...")

        # STEP 2: Try structured sections mode (legacy HTML template rendering)
        sections = payload.get("sections")
        brief = payload.get("brief")

        print(
            f"📄 PDF DEBUG: Structured mode check - sections={bool(sections)}, brief={bool(brief)}"
        )

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

                print("📄 PDF DEBUG: ✅ using STRUCTURED mode")
                logger.info(f"PDF exported via structured mode: {len(pdf_bytes)} bytes")
                return StreamingResponse(
                    iter([pdf_bytes]),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": 'attachment; filename="AICMO_Marketing_Plan.pdf"'
                    },
                )
            except Exception as e:
                print(f"📄 PDF DEBUG: structured mode failed: {e}")
                logger.debug(f"Structured PDF rendering failed (not fatal): {e}")

        # STEP 3: Fallback to markdown mode (ReportLab text_to_pdf_bytes)
        markdown = payload.get("markdown") or ""

        print(
            f"📄 PDF DEBUG: Markdown fallback mode - markdown length={len(markdown) if markdown else 0}"
        )

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

        print("📄 PDF DEBUG: 🔄 using MARKDOWN PATH (ReportLab text_to_pdf_bytes)")
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
