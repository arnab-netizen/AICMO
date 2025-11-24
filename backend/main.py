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
from backend.agency_grade_enhancers import apply_agency_grade_enhancements  # noqa: E402
from backend.export_utils import safe_export_pdf, safe_export_pptx, safe_export_zip  # noqa: E402
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

# Configure structured logging
from aicmo.logging import configure_logging, get_logger  # noqa: E402

configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

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
    industry_key: Optional[str] = None  # Phase 5: Optional industry preset key
    package_preset: Optional[str] = None  # TURBO: package name
    include_agency_grade: bool = False  # TURBO: enable agency-grade enhancements
    use_learning: bool = False  # Phase L: enable learning context retrieval and injection
    wow_enabled: bool = True  # WOW: Enable WOW template wrapping
    wow_package_key: Optional[str] = None  # WOW: Package key (e.g., "quick_social_basic")


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
    cb = CampaignBlueprintView(
        big_idea=f"Whenever your ideal buyer thinks of {big_idea_industry}, they remember {b.brand_name} first.",
        objective=CampaignObjectiveView(
            primary=g.primary_goal or "brand_awareness",
            secondary=g.secondary_goal,
        ),
        audience_persona=AudiencePersonaView(
            name="Core Buyer",
            description=(
                f"{a.primary_customer} who is actively looking for better options and wants "
                "less friction, more clarity, and trustworthy proof before committing."
            ),
        ),
    )

    # Social calendar (7 days) - brief-driven hooks and CTAs
    posts = generate_social_calendar(req.brief, start_date=today, days=7)

    cal = SocialCalendarView(
        start_date=today,
        end_date=today + timedelta(days=6),
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
        preset = PACKAGE_PRESETS.get(req.package_preset)
        if preset:
            # Generate content for all sections in the preset
            for section_id in preset.get("sections", []):
                # Map section IDs to generated content from existing output blocks
                section_content = _generate_section_content(
                    section_id, req, mp, cb, cal, pr, creatives, persona_cards, action_plan
                )
                extra_sections[section_id] = section_content

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

    Non-breaking: if WOW fails or is disabled, output is returned unchanged.
    """
    if not req.wow_enabled or not req.wow_package_key:
        return output

    try:
        # Fetch the WOW rule for this package (contains section structure)
        wow_rule = get_wow_rule(req.wow_package_key)
        sections = wow_rule.get("sections", [])

        # Debug: Log which WOW pack and sections are being used
        print(f"[WOW DEBUG] Using WOW pack: {req.wow_package_key}")
        print(f"[WOW DEBUG] Sections in WOW rule: {[s['key'] for s in sections]}")

        # Build the WOW report using the new unified system
        wow_markdown = build_wow_report(req=req, wow_rule=wow_rule)

        # Store in output
        output.wow_markdown = wow_markdown
        output.wow_package_key = req.wow_package_key

        logger.debug(f"WOW report built successfully: {req.wow_package_key}")
        logger.info(f"WOW system used {len(sections)} sections for {req.wow_package_key}")
    except Exception as e:
        logger.warning(f"WOW report building failed (non-critical): {e}")
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

        # Phase L: Auto-learn from this final report
        try:
            learn_from_report(
                report=base_output,
                project_id=None,  # No explicit project ID in this context
                tags=["auto_learn", "final_report"],
            )
            logger.info("🔥 [LEARNING RECORDED] Report learned and stored in memory engine")
        except Exception as e:
            logger.debug(f"Auto-learning failed (non-critical): {e}")
            logger.warning("⚠️  [LEARNING FAILED] Report could not be recorded: %s", str(e))

        # WOW: Apply optional template wrapping
        base_output = _apply_wow_to_output(base_output, req)

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

        # Phase L: Auto-learn from this final report
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

        # Phase L: Auto-learn from this final report (even on fallback)
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

        # Phase L: Auto-learn from this final report (even on fallback)
        try:
            learn_from_report(
                report=base_output,
                project_id=None,
                tags=["auto_learn", "final_report", "llm_fallback"],
            )
        except Exception as e:
            print(f"[AICMO] Auto-learning failed (non-critical): {e}")

        # WOW: Apply optional template wrapping
        base_output = _apply_wow_to_output(base_output, req)

        return base_output


@app.post("/api/aicmo/generate_report")
async def api_aicmo_generate_report(payload: dict) -> dict:
    """
    Streamlit-compatible wrapper endpoint for /aicmo/generate.

    Converts Streamlit's payload structure to GenerateRequest and calls the core endpoint.
    Expected Streamlit payload format:
    {
        "stage": "draft|refine|final",
        "client_brief": {...dict with client metadata...},
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
    # 🔥 DEBUG: Log package preset received
    package_name = payload.get("package_name")
    print("\n" + "=" * 60)
    print("🔥 DEBUG PACKAGE PRESET RECEIVED")
    print(f"    package_name: {package_name}")

    # Check presets
    preset_config = PACKAGE_PRESETS.get(package_name)
    print(f"    preset_config: {preset_config}")
    if preset_config:
        print(f"    sections: {preset_config.get('sections')}")
        print(f"    complexity: {preset_config.get('complexity')}")
        print(f"    requires_research: {preset_config.get('requires_research')}")
    print("=" * 60 + "\n")

    try:
        # Extract client brief dict
        client_brief_dict = payload.get("client_brief", {})

        # Convert dict to ClientInputBrief model
        brief = ClientInputBrief(
            client_name=client_brief_dict.get("client_name"),
            brand_name=client_brief_dict.get("brand_name"),
            product_service=client_brief_dict.get("product_service"),
            industry=client_brief_dict.get("industry"),
            geography=client_brief_dict.get("geography"),
            objectives=client_brief_dict.get("objectives"),
            budget=client_brief_dict.get("budget"),
            timeline=client_brief_dict.get("timeline"),
            constraints=client_brief_dict.get("constraints"),
        )

        # Extract services dict
        services = payload.get("services", {})
        include_agency_grade = services.get("include_agency_grade", False)

        # Extract use_learning flag
        use_learning = payload.get("use_learning", False)

        # Extract wow settings
        wow_enabled = payload.get("wow_enabled", False)
        wow_package_key = payload.get("wow_package_key")

        # 🔧 TEMPORARY TROUBLESHOOTING: Force WOW bypass for strategy_campaign_standard
        # to verify if the underlying generator produces a long-form report
        package_name = payload.get("package_name")
        if package_name == "Strategy + Campaign Pack (Standard)":
            # TEMP: Disable WOW to see raw generator output
            wow_enabled = False
            wow_package_key = None
            logger.info(
                "🔧 [TEMPORARY] WOW disabled for strategy_campaign_standard - testing raw output"
            )

        # Extract industry key
        industry_key = payload.get("industry_key")

        # Build GenerateRequest
        gen_req = GenerateRequest(
            brief=brief,
            generate_marketing_plan=services.get("marketing_plan", True),
            generate_campaign_blueprint=services.get("campaign_blueprint", True),
            generate_social_calendar=services.get("social_calendar", True),
            generate_performance_review=services.get("performance_review", False),
            generate_creatives=services.get("creatives", True),
            package_preset=payload.get("package_name"),
            include_agency_grade=include_agency_grade,
            use_learning=use_learning,
            wow_enabled=wow_enabled,
            wow_package_key=wow_package_key,
            industry_key=industry_key,
        )

        # Call the core /aicmo/generate endpoint
        report = await aicmo_generate(gen_req)

        # Convert output to markdown
        report_markdown = generate_output_report_markdown(brief, report)

        # 🔍 DEBUG: Log report length and tail (before returning to Streamlit)
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG REPORT LENGTH: {len(report_markdown)} characters")
        print(f"{'='*60}")
        print("LAST 500 CHARACTERS:")
        print(report_markdown[-500:] if len(report_markdown) > 500 else report_markdown)
        print(f"{'='*60}\n")

        logger.info(
            f"✅ [API WRAPPER] generate_report call successful. "
            f"include_agency_grade={include_agency_grade}, use_learning={use_learning} "
            f"report_length={len(report_markdown)}"
        )

        return {
            "report_markdown": report_markdown,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"❌ [API WRAPPER] generate_report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


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


@app.post("/aicmo/export/pdf")
def aicmo_export_pdf(payload: dict):
    """
    Convert markdown or structured sections to PDF with safe error handling.

    Supports two modes:
    1. Markdown mode: { "markdown": "..." }
    2. Structured mode: { "sections": [...], "brief": {...} }

    Returns:
        StreamingResponse with PDF on success (Content-Type: application/pdf).
        JSONResponse with error details on failure (Content-Type: application/json).
    """
    try:
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
