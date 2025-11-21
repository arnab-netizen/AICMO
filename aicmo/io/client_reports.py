"""AICMO IO Layer – Client Reports, Briefs, and Output Models."""

from __future__ import annotations

from datetime import date
from textwrap import dedent
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field


# =========================================
# INPUT SIDE – Operator-friendly brief model
# =========================================


class BrandBrief(BaseModel):
    brand_name: str
    website: Optional[HttpUrl] = None
    social_links: List[HttpUrl] = Field(default_factory=list)
    industry: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    business_type: Optional[str] = None
    description: Optional[str] = None


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


# =========================================
# OUTPUT SIDE – AICMO composite report model
# (shaped to match your Streamlit code)
# =========================================


class StrategyPillar(BaseModel):
    name: str
    description: Optional[str] = None
    kpi_impact: Optional[str] = None


class MarketingPlanView(BaseModel):
    executive_summary: str
    situation_analysis: str
    strategy: str
    pillars: List[StrategyPillar] = Field(default_factory=list)


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


class CreativesBlock(BaseModel):
    notes: Optional[str] = None
    hooks: List[str] = Field(default_factory=list)
    captions: List[str] = Field(default_factory=list)
    scripts: List[str] = Field(default_factory=list)


class AICMOOutputReport(BaseModel):
    marketing_plan: MarketingPlanView
    campaign_blueprint: CampaignBlueprintView
    social_calendar: SocialCalendarView
    performance_review: Optional[PerformanceReviewView] = None
    creatives: Optional[CreativesBlock] = None


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

        ## 2. Strategic Marketing Plan

        ### 2.1 Executive Summary

        {mp.executive_summary}

        ### 2.2 Situation Analysis

        {mp.situation_analysis}

        ### 2.3 Strategy

        {mp.strategy}

        ### 2.4 Strategic Pillars

        """
    ).strip()

    if mp.pillars:
        for p in mp.pillars:
            md += (
                f"\n- **{p.name}** – {p.description or ''} "
                f"_(KPI impact: {p.kpi_impact or 'N/A'})_"
            )
    else:
        md += "\n_No explicit pillars defined._"

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

    if output.creatives:
        cr = output.creatives
        md += "\n\n---\n\n## 6. Creatives & Assets\n"
        if cr.notes:
            md += f"\n{cr.notes}\n"
        if cr.hooks:
            md += "\n**Hooks:**\n"
            for h in cr.hooks:
                md += f"- {h}\n"
        if cr.captions:
            md += "\n**Captions:**\n"
            for c in cr.captions:
                md += f"- {c}\n"
        if cr.scripts:
            md += "\n**Scripts:**\n"
            for stext in cr.scripts:
                md += f"- {stext}\n"

    return md.strip()
