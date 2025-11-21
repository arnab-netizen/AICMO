"""Canonical AICMO Input & Output Models."""

from __future__ import annotations

from datetime import date
from typing import List, Optional, Literal

from pydantic import BaseModel, HttpUrl, Field


# ==============
# INPUT SIDE
# ==============


class SocialLink(BaseModel):
    label: str  # e.g. "Website", "Instagram"
    url: HttpUrl


class BrandBasics(BaseModel):
    brand_name: str
    website: Optional[HttpUrl] = None
    social_links: List[SocialLink] = Field(default_factory=list)
    industry: str
    locations: List[str] = Field(default_factory=list)
    business_type: Literal["B2B", "B2C", "Hybrid"] = "B2C"
    description_short: Optional[str] = None


class AudienceInfo(BaseModel):
    primary_customer_description: str
    secondary_customer_description: Optional[str] = None
    pain_points: List[str] = Field(default_factory=list)
    online_hangouts: List[
        Literal["LinkedIn", "Instagram", "Facebook", "X", "YouTube", "WhatsApp", "Other"]
    ] = Field(default_factory=list)


class GoalInfo(BaseModel):
    primary_goal: Literal[
        "brand_awareness",
        "leads",
        "sales",
        "app_installs",
        "event_signups",
        "community_growth",
    ]
    secondary_goal: Optional[str] = None
    goal_timeline: Literal["1_month", "3_months", "6_months", "ongoing"] = "3_months"
    important_kpis: List[str] = Field(default_factory=list)  # e.g. ["reach", "engagement", "leads"]


class BrandVoice(BaseModel):
    tone_of_voice: List[
        Literal["professional", "friendly", "bold", "emotional", "humorous", "serious"]
    ] = Field(default_factory=list)
    has_brand_guidelines: bool = False
    brand_guideline_url: Optional[HttpUrl] = None
    preferred_colors_or_style: Optional[str] = None
    competitors_liked: List[HttpUrl] = Field(default_factory=list)
    competitors_disliked: List[HttpUrl] = Field(default_factory=list)


class ProductService(BaseModel):
    name: str
    usp: Optional[str] = None
    pricing_note: Optional[str] = None


class ProductServiceInfo(BaseModel):
    top_offers: Optional[str] = None
    testimonials_or_proof: Optional[str] = None
    products: List[ProductService] = Field(default_factory=list)


class ExistingAssetsConstraints(BaseModel):
    already_posting: bool = False
    existing_social_links: List[SocialLink] = Field(default_factory=list)
    content_that_worked: Optional[str] = None
    content_that_failed: Optional[str] = None
    constraints: List[str] = Field(
        default_factory=list
    )  # e.g. ["no_paid_ads", "no_aggressive_tone"]
    focus_platforms: List[str] = Field(default_factory=list)
    avoid_platforms: List[str] = Field(default_factory=list)


class OperationalDetails(BaseModel):
    approval_cadence: Literal["daily", "weekly", "monthly", "auto_approve"] = "weekly"
    needs_content_calendar: bool = True
    needs_posting_and_scheduling: bool = True
    upcoming_events_or_seasonality: Optional[str] = None
    promo_budget_band: Literal["0", "5k_20k", "20k_1L", "gt_1L"] = "0"


class StrategicInputs(BaseModel):
    brand_adjectives: List[str] = Field(
        default_factory=list
    )  # e.g. ["trustworthy", "bold", "local"]
    success_in_30_days: Optional[str] = None
    must_include_messages: Optional[str] = None
    must_avoid_messages: Optional[str] = None
    tagline: Optional[str] = None
    extra_notes: Optional[str] = None


class ClientIntakeForm(BaseModel):
    """Canonical AICMO client input schema."""

    brand: BrandBasics
    audience: AudienceInfo
    goals: GoalInfo
    voice: BrandVoice
    product_info: ProductServiceInfo
    existing_assets: ExistingAssetsConstraints
    operations: OperationalDetails
    strategy_inputs: StrategicInputs


# ==============
# OUTPUT SIDE – REPORTS
# ==============


class SituationAnalysis(BaseModel):
    audience_summary: str
    market_context: str
    competitors_snapshot: str
    key_insights: str


class StrategyBlock(BaseModel):
    core_message: str
    value_proposition: str
    differentiators: List[str]
    positioning_statement: str


class Pillar(BaseModel):
    name: str
    description: str
    kpi_impact: str  # e.g. "Drives awareness + engagement"


class ChannelStrategy(BaseModel):
    channel: str  # "LinkedIn", "Instagram", etc.
    purpose: str
    content_types: List[str]  # e.g. ["carousels", "reels"]
    frequency: str  # e.g. "3x per week"
    kpis: List[str]


class MarketingPlanReport(BaseModel):
    """Standard strategic marketing plan report."""

    brand_name: str
    timeframe: str  # e.g. "Q1 2026"
    executive_summary: str
    situation_analysis: SituationAnalysis
    strategy: StrategyBlock
    pillars: List[Pillar]
    channel_strategies: List[ChannelStrategy]
    risks_and_mitigations: str


class CampaignObjective(BaseModel):
    primary_objective: str
    secondary_objective: Optional[str] = None
    kpi_model: str


class AudiencePersona(BaseModel):
    name: str
    demographics: str
    psychographics: str
    pain_points: str
    motivations: str


class CreativeDirection(BaseModel):
    hooks: List[str]
    messages: List[str]
    visual_style: str
    emotional_triggers: List[str]


class ExecutionPlan(BaseModel):
    platform_strategies: str  # free-form description
    posting_level: str  # e.g. "high frequency" etc.
    formats: List[str]  # e.g. ["reels", "stories", "static"]


class BudgetInfo(BaseModel):
    note: str
    paid_vs_organic_split: Optional[str] = None


class CampaignBlueprintReport(BaseModel):
    """Standard campaign strategy report."""

    campaign_name: str
    brand_name: str
    objective: CampaignObjective
    big_idea: str
    audience_persona: Optional[AudiencePersona] = None
    creative_direction: CreativeDirection
    execution_plan: ExecutionPlan
    budget: Optional[BudgetInfo] = None


class CalendarPost(BaseModel):
    date: date
    platform: str
    theme: str
    hook: str
    call_to_action: str
    asset_type: str  # e.g. "reel", "static_post", "email_newsletter"
    status: Literal["planned", "draft", "approved", "published"] = "planned"
    notes: Optional[str] = None


class SocialCalendarReport(BaseModel):
    """Weekly or monthly social/content calendar."""

    brand_name: str
    period_label: str  # e.g. "March 2026"
    posts: List[CalendarPost]


class ChannelPerformance(BaseModel):
    channel: str
    reach: Optional[int] = None
    impressions: Optional[int] = None
    engagement: Optional[int] = None
    clicks: Optional[int] = None
    leads: Optional[int] = None
    conversions: Optional[int] = None
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    notes: Optional[str] = None


class PerformanceHighlights(BaseModel):
    wins: str
    failures: str
    opportunities: str


class PerformanceRecommendations(BaseModel):
    do_more_of: str
    do_less_of: str
    experiments: str


class PerformanceReviewReport(BaseModel):
    """Monthly performance/KPI report."""

    brand_name: str
    period_label: str  # e.g. "February 2026"
    summary: str
    channel_performance: List[ChannelPerformance]
    highlights: PerformanceHighlights
    recommendations: PerformanceRecommendations
