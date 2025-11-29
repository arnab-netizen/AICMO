from __future__ import annotations

from datetime import date
from textwrap import dedent
from typing import List, Optional, Dict

from pydantic import BaseModel, HttpUrl, Field


# =========================================
# INPUT SIDE – Operator-friendly brief model
# =========================================


class BrandBrief(BaseModel):
    # Core required fields
    brand_name: str
    industry: str
    product_service: str

    # Goal and audience
    primary_goal: str
    primary_customer: str
    secondary_customer: Optional[str] = None

    # Brand character
    brand_tone: Optional[str] = None

    # Location and timing
    location: Optional[str] = None
    timeline: Optional[str] = None

    # Competitors and context
    competitors: List[str] = Field(default_factory=list)

    # Web and social
    website: Optional[HttpUrl] = None
    social_links: List[HttpUrl] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    business_type: Optional[str] = None
    description: Optional[str] = None

    def with_safe_defaults(self) -> "BrandBrief":
        """
        Return a copy where essential fields have sensible fallbacks.
        Used by downstream WOW / agency modules to avoid attribute errors
        and 'Not specified' placeholders.
        """

        def _fallback(value: Optional[str], default: str) -> str:
            v = (value or "").strip()
            return v if v else default

        return BrandBrief(
            brand_name=_fallback(self.brand_name, "Your Brand"),
            industry=_fallback(self.industry, "your industry"),
            product_service=_fallback(self.product_service, "your main product/service"),
            primary_goal=_fallback(self.primary_goal, "growth and market expansion"),
            primary_customer=_fallback(self.primary_customer, "your core customer segment"),
            secondary_customer=self.secondary_customer,
            brand_tone=_fallback(self.brand_tone, "professional and engaging"),
            location=_fallback(self.location, "your location"),
            timeline=_fallback(self.timeline, "the next 30–90 days"),
            competitors=self.competitors or [],
            website=self.website,
            social_links=self.social_links or [],
            locations=self.locations or [],
            business_type=self.business_type,
            description=self.description,
        )


class AudienceBrief(BaseModel):
    primary_customer: str
    secondary_customer: Optional[str] = None
    pain_points: List[str] = Field(default_factory=list)
    online_hangouts: List[str] = Field(default_factory=list)


class GoalBrief(BaseModel):
    primary_goal: str
    secondary_goal: Optional[str] = None
    timeline: Optional[str] = None
    kpis: List[str] = Field(default_factory=list)


class VoiceBrief(BaseModel):
    tone_of_voice: List[str] = Field(default_factory=list)
    has_guidelines: bool = False
    guidelines_link: Optional[HttpUrl] = None
    preferred_colors: Optional[str] = None
    competitors_like: List[HttpUrl] = Field(default_factory=list)
    competitors_dislike: List[HttpUrl] = Field(default_factory=list)


class ProductServiceItem(BaseModel):
    name: str
    usp: Optional[str] = None
    pricing_note: Optional[str] = None


class ProductServiceBrief(BaseModel):
    items: List[ProductServiceItem] = Field(default_factory=list)
    current_offers: Optional[str] = None
    testimonials_or_proof: Optional[str] = None


class AssetsConstraintsBrief(BaseModel):
    already_posting: bool = False
    current_social_links: List[HttpUrl] = Field(default_factory=list)
    content_that_worked: Optional[str] = None
    content_that_failed: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    focus_platforms: List[str] = Field(default_factory=list)
    avoid_platforms: List[str] = Field(default_factory=list)
    geography: Optional[str] = None  # Geographic targeting/launch location
    budget: Optional[str] = None  # Budget information
    timeline: Optional[str] = None  # Timeline/deadline information


class OperationsBrief(BaseModel):
    approval_frequency: Optional[str] = None
    needs_calendar: bool = True
    wants_posting_and_scheduling: bool = False
    upcoming_events: Optional[str] = None
    promo_budget_range: Optional[str] = None


class StrategyExtrasBrief(BaseModel):
    brand_adjectives: List[str] = Field(default_factory=list)
    success_30_days: Optional[str] = None
    must_include_messages: Optional[str] = None
    must_avoid_messages: Optional[str] = None
    tagline: Optional[str] = None
    extra_notes: Optional[str] = None


class ClientInputBrief(BaseModel):
    """Operator-facing structured brief used by Streamlit + backend."""

    brand: BrandBrief
    audience: AudienceBrief
    goal: GoalBrief
    voice: VoiceBrief
    product_service: ProductServiceBrief
    assets_constraints: AssetsConstraintsBrief
    operations: OperationsBrief
    strategy_extras: StrategyExtrasBrief

    def with_safe_defaults(self) -> "ClientInputBrief":
        """
        Return a copy where brand and goal fields use safe defaults.
        Prevents 'Not specified' and attribute errors downstream.
        """
        return ClientInputBrief(
            brand=self.brand.with_safe_defaults(),
            audience=self.audience,
            goal=self.goal,
            voice=self.voice,
            product_service=self.product_service,
            assets_constraints=self.assets_constraints,
            operations=self.operations,
            strategy_extras=self.strategy_extras,
        )


# =========================================
# OUTPUT SIDE – AICMO composite report model
# =========================================


class StrategyPillar(BaseModel):
    name: str
    description: Optional[str] = None
    kpi_impact: Optional[str] = None


class MessagingPyramid(BaseModel):
    promise: str
    key_messages: List[str] = Field(default_factory=list)
    proof_points: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)


class SWOTBlock(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class CompetitorSnapshot(BaseModel):
    narrative: str
    common_patterns: List[str] = Field(default_factory=list)
    differentiation_opportunities: List[str] = Field(default_factory=list)


class MarketingPlanView(BaseModel):
    executive_summary: str
    situation_analysis: str
    strategy: str
    pillars: List[StrategyPillar] = Field(default_factory=list)
    messaging_pyramid: Optional[MessagingPyramid] = None
    swot: Optional[SWOTBlock] = None
    competitor_snapshot: Optional[CompetitorSnapshot] = None


class CampaignObjectiveView(BaseModel):
    primary: str
    secondary: Optional[str] = None


class AudiencePersonaView(BaseModel):
    name: str
    description: Optional[str] = None


class CampaignBlueprintView(BaseModel):
    big_idea: str
    objective: CampaignObjectiveView
    audience_persona: Optional[AudiencePersonaView] = None


class CalendarPostView(BaseModel):
    date: date
    platform: str
    theme: str
    hook: str
    cta: str
    asset_type: str
    status: Optional[str] = None


class SocialCalendarView(BaseModel):
    start_date: date
    end_date: date
    posts: List[CalendarPostView] = Field(default_factory=list)


class PerfSummaryView(BaseModel):
    growth_summary: str
    wins: str
    failures: str
    opportunities: str


class PerformanceReviewView(BaseModel):
    summary: PerfSummaryView


class CreativeRationale(BaseModel):
    strategy_summary: str
    psychological_triggers: List[str] = Field(default_factory=list)
    audience_fit: str
    risk_notes: Optional[str] = None


class ChannelVariant(BaseModel):
    platform: str
    format: str
    hook: str
    caption: str


class ToneVariant(BaseModel):
    tone_label: str
    example_caption: str


class HookInsight(BaseModel):
    hook: str
    insight: str


class CTAVariant(BaseModel):
    label: str
    text: str
    usage_context: str


class OfferAngle(BaseModel):
    label: str
    description: str
    example_usage: str


class PersonaCard(BaseModel):
    # Required headline fields
    name: str

    # Optional fields with safe defaults to tolerate partial LLM-generated personas
    demographics: str = ""
    psychographics: str = ""
    tone_preference: str = ""
    pain_points: List[str] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list)
    objections: List[str] = Field(default_factory=list)
    content_preferences: List[str] = Field(default_factory=list)
    primary_platforms: List[str] = Field(default_factory=list)


class ActionPlan(BaseModel):
    quick_wins: List[str] = Field(default_factory=list)
    next_10_days: List[str] = Field(default_factory=list)
    next_30_days: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class CreativesBlock(BaseModel):
    notes: Optional[str] = None
    hooks: List[str] = Field(default_factory=list)
    captions: List[str] = Field(default_factory=list)
    scripts: List[str] = Field(default_factory=list)
    rationale: Optional[CreativeRationale] = None
    channel_variants: List[ChannelVariant] = Field(default_factory=list)
    email_subject_lines: List[str] = Field(default_factory=list)
    tone_variants: List[ToneVariant] = Field(default_factory=list)
    hook_insights: List[HookInsight] = Field(default_factory=list)
    cta_library: List[CTAVariant] = Field(default_factory=list)
    offer_angles: List[OfferAngle] = Field(default_factory=list)


class AICMOOutputReport(BaseModel):
    marketing_plan: MarketingPlanView
    campaign_blueprint: CampaignBlueprintView
    social_calendar: SocialCalendarView
    performance_review: Optional[PerformanceReviewView] = None
    creatives: Optional[CreativesBlock] = None
    persona_cards: List[PersonaCard] = Field(default_factory=list)
    action_plan: Optional[ActionPlan] = None
    # TURBO: agency-grade extra sections (title → markdown body)
    extra_sections: Dict[str, str] = Field(default_factory=dict)
    # Auto-detected competitors via OSM or Google Places
    auto_detected_competitors: Optional[List[Dict]] = None
    # Competitor visual benchmark (auto-detected or user-uploaded)
    competitor_visual_benchmark: Optional[List[Dict]] = None
    # WOW: Optional markdown wrapped in WOW template
    wow_markdown: Optional[str] = None
    wow_package_key: Optional[str] = None


# =========================================
# Markdown generator for final client report
# =========================================


def generate_output_report_markdown(
    brief: ClientInputBrief,
    output: AICMOOutputReport,
) -> str:
    """Convert brief + output into a single client-facing Markdown report."""
    b = brief.brand
    g = brief.goal
    a = brief.audience
    s = brief.strategy_extras

    mp = output.marketing_plan
    cb = output.campaign_blueprint
    cal = output.social_calendar
    pr = output.performance_review
    cr = output.creatives

    brand_name = b.brand_name or "Client"

    md = dedent(
        f"""
        # AICMO Marketing & Campaign Report – {brand_name}

        ## 1. Brand & Objectives

        **Brand:** {b.brand_name}  
        **Industry:** {b.industry or "Not specified"}  
        **Primary goal:** {g.primary_goal or "Not specified"}  
        **Timeline:** {g.timeline or "Not specified"}

        **Primary customer:** {a.primary_customer}  
        **Secondary customer:** {a.secondary_customer or "Not specified"}

        **Brand adjectives:** {", ".join(s.brand_adjectives) if s.brand_adjectives else "Not specified"}

        ---
        """
    ).strip()

    # --- Strategic Marketing Plan ---
    md += dedent(
        """

        ## 2. Strategic Marketing Plan

        ### 2.1 Executive Summary

        """
    )
    md += f"\n{mp.executive_summary}\n"

    md += dedent(
        """

        ### 2.2 Situation Analysis

        """
    )
    md += f"\n{mp.situation_analysis}\n"

    md += dedent(
        """

        ### 2.3 Strategy

        """
    )
    md += f"\n{mp.strategy}\n"

    md += "\n### 2.4 Strategic Pillars\n\n"
    if mp.pillars:
        for p in mp.pillars:
            md += (
                f"- **{p.name}** – {p.description or ''} _(KPI impact: {p.kpi_impact or 'N/A'})_\n"
            )
    else:
        md += "_No explicit pillars defined._\n"

    if mp.messaging_pyramid:
        mpyr = mp.messaging_pyramid
        md += "\n### 2.5 Brand messaging pyramid\n\n"
        md += f"**Brand promise:** {mpyr.promise}\n\n"
        if mpyr.key_messages:
            md += "**Key messages:**\n"
            for msg in mpyr.key_messages:
                md += f"- {msg}\n"
        if mpyr.proof_points:
            md += "\n**Proof points:**\n"
            for p in mpyr.proof_points:
                md += f"- {p}\n"
        if mpyr.values:
            md += "\n**Values / personality:**\n"
            for v in mpyr.values:
                md += f"- {v}\n"

    if mp.swot:
        sw = mp.swot
        md += "\n### 2.6 SWOT snapshot\n\n"
        md += "**Strengths**\n"
        for x in sw.strengths:
            md += f"- {x}\n"
        md += "\n**Weaknesses**\n"
        for x in sw.weaknesses:
            md += f"- {x}\n"
        md += "\n**Opportunities**\n"
        for x in sw.opportunities:
            md += f"- {x}\n"
        md += "\n**Threats**\n"
        for x in sw.threats:
            md += f"- {x}\n"

    if mp.competitor_snapshot:
        cs = mp.competitor_snapshot
        md += "\n### 2.7 Competitor snapshot\n\n"
        md += f"{cs.narrative}\n\n"
        if cs.common_patterns:
            md += "**Common patterns:**\n"
            for ptn in cs.common_patterns:
                md += f"- {ptn}\n"
        if cs.differentiation_opportunities:
            md += "\n**Differentiation opportunities:**\n"
            for opp in cs.differentiation_opportunities:
                md += f"- {opp}\n"

    # --- Campaign Blueprint ---
    md += dedent(
        """

        ---

        ## 3. Campaign Blueprint

        ### 3.1 Big Idea

        """
    )
    md += f"\n{cb.big_idea}\n"

    md += "\n### 3.2 Objectives\n"
    md += f"- Primary: {cb.objective.primary}\n"
    if cb.objective.secondary:
        md += f"- Secondary: {cb.objective.secondary}\n"

    if cb.audience_persona:
        ap = cb.audience_persona
        md += "\n### 3.3 Audience Persona\n"
        md += f"**{ap.name}**\n\n"
        md += f"{ap.description or ''}\n"

    if output.persona_cards:
        md += "\n### 3.4 Detailed persona cards\n\n"
        for p in output.persona_cards:
            md += f"**{p.name}**\n\n"
            md += f"- Demographics: {p.demographics}\n"
            md += f"- Psychographics: {p.psychographics}\n"
            if p.pain_points:
                md += f"- Pain points: {', '.join(p.pain_points)}\n"
            if p.triggers:
                md += f"- Triggers: {', '.join(p.triggers)}\n"
            if p.objections:
                md += f"- Objections: {', '.join(p.objections)}\n"
            if p.content_preferences:
                md += f"- Content preferences: {', '.join(p.content_preferences)}\n"
            if p.primary_platforms:
                md += f"- Primary platforms: {', '.join(p.primary_platforms)}\n"
            md += f"- Tone preference: {p.tone_preference}\n\n"

    # --- Calendar ---
    md += dedent(
        f"""

        ---

        ## 4. Content Calendar

        Period: **{cal.start_date} → {cal.end_date}**

        | Date | Platform | Theme | Hook | CTA | Asset Type | Status |
        |------|----------|-------|------|-----|------------|--------|
        """
    )

    for p in cal.posts:
        md += (
            f"| {p.date} | {p.platform} | {p.theme} | {p.hook} | "
            f"{p.cta} | {p.asset_type} | {p.status or ''} |\n"
        )

    # --- Performance Review ---
    if pr:
        md += dedent(
            f"""

            ---

            ## 5. Performance Review

            ### 5.1 Growth Summary

            {pr.summary.growth_summary}

            ### 5.2 Wins

            {pr.summary.wins}

            ### 5.3 Failures

            {pr.summary.failures}

            ### 5.4 Opportunities

            {pr.summary.opportunities}
            """
        )

    # --- Action Plan ---
    if output.action_plan:
        ap = output.action_plan
        md += "\n\n---\n\n## 6. Next 30 days – Action plan\n\n"
        if ap.quick_wins:
            md += "**Quick wins:**\n"
            for item in ap.quick_wins:
                md += f"- {item}\n"
        if ap.next_10_days:
            md += "\n**Next 10 days:**\n"
            for item in ap.next_10_days:
                md += f"- {item}\n"
        if ap.next_30_days:
            md += "\n**Next 30 days:**\n"
            for item in ap.next_30_days:
                md += f"- {item}\n"
        if ap.risks:
            md += "\n**Risks & watchouts:**\n"
            for item in ap.risks:
                md += f"- {item}\n"

    # --- Creatives ---
    if cr:
        md += "\n\n---\n\n## 7. Creatives & Multi-Channel Adaptation\n"

        if cr.rationale:
            md += "\n### 7.1 Creative rationale\n\n"
            md += f"{cr.rationale.strategy_summary}\n\n"
            if cr.rationale.psychological_triggers:
                md += "**Psychological triggers used:**\n"
                for t in cr.rationale.psychological_triggers:
                    md += f"- {t}\n"
            md += f"\n**Audience fit:** {cr.rationale.audience_fit}\n"
            if cr.rationale.risk_notes:
                md += f"\n**Risks / guardrails:** {cr.rationale.risk_notes}\n"

        if cr.channel_variants:
            md += "\n### 7.2 Platform-specific variants\n\n"
            md += "| Platform | Format | Hook | Caption |\n"
            md += "|----------|--------|------|---------|\n"
            for v in cr.channel_variants:
                md += (
                    f"| {v.platform} | {v.format} | {v.hook} | "
                    f"{v.caption.replace('|', '/')} |\n"
                )

        if cr.email_subject_lines:
            md += "\n### 7.3 Email subject lines\n\n"
            for sline in cr.email_subject_lines:
                md += f"- {sline}\n"

        if cr.tone_variants:
            md += "\n### 7.4 Tone/style variants\n\n"
            for tv in cr.tone_variants:
                md += f"- **{tv.tone_label}:** {tv.example_caption}\n"

        if cr.hook_insights:
            md += "\n### 7.5 Hook insights (why these work)\n\n"
            for hi in cr.hook_insights:
                md += f"- **{hi.hook}** – {hi.insight}\n"

        if cr.cta_library:
            md += "\n### 7.6 CTA library\n\n"
            for cta in cr.cta_library:
                md += f"- **{cta.label}:** {cta.text} _(Use: {cta.usage_context})_\n"

        if cr.offer_angles:
            md += "\n### 7.7 Offer angles\n\n"
            for angle in cr.offer_angles:
                md += f"- **{angle.label}:** {angle.description}\n"
                md += f"  - Example: {angle.example_usage}\n"

        if cr.hooks:
            md += "\n### 7.8 Generic hooks\n\n"
            for h in cr.hooks:
                md += f"- {h}\n"

        if cr.captions:
            md += "\n### 7.9 Generic captions\n\n"
            for c in cr.captions:
                md += f"- {c}\n"

        if cr.scripts:
            md += "\n### 7.10 Ad script snippets\n\n"
            for stext in cr.scripts:
                md += f"- {stext}\n"

    # --- Agency-Grade TURBO Sections ---
    if output.extra_sections:
        md += "\n\n---\n\n# Agency-Grade Strategic Add-ons\n"
        for title, body in output.extra_sections.items():
            if not body:
                continue
            md += f"\n## {title}\n\n{body.strip()}\n"

    # ✨ FIX #2 & #5 & #8: Apply quality guardrails and formatting pass (import locally to avoid circular imports)
    from aicmo.presets.quality_enforcer import enforce_quality
    from aicmo.generators.output_formatter import format_final_output

    brief_dict = {
        "brand_name": brief.brand.brand_name,
        "industry": brief.brand.industry,
        "objectives": brief.goal.primary_goal,
    }
    md = enforce_quality(brief_dict, md.strip())
    md = format_final_output(md)

    return md
