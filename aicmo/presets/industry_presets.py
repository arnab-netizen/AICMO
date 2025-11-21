"""Industry presets for AICMO content generation.

Pre-configured industry context for 4 key verticals:
- B2B SaaS: LinkedIn, Email, YouTube → ROI/efficiency focus
- eCommerce/D2C: Instagram Reels, UGC, Meta → ROAS/repeat purchase
- Local Service: Instagram, Maps, WhatsApp → footfall/bookings
- Coaching: YouTube, Webinars, Email → authority/transformation
"""

from dataclasses import dataclass
from typing import List


@dataclass
class IndustryPreset:
    """Pre-configured context for a specific industry vertical."""

    name: str
    description: str
    strategy_notes: List[str]
    priority_channels: List[str]
    sample_kpis: List[str]
    creative_angles: List[str]
    common_objections: List[str]
    default_tone: str


# B2B SaaS Preset
B2B_SAAS = IndustryPreset(
    name="B2B SaaS",
    description="Business software and services targeting other businesses",
    strategy_notes=[
        "Focus on ROI and efficiency gains",
        "Emphasize implementation speed and integration",
        "Target decision-makers and economic buyers",
        "Lead nurturing is critical—long sales cycles",
        "Build thought leadership and industry credibility",
    ],
    priority_channels=["LinkedIn", "Email", "YouTube", "X"],
    sample_kpis=["Qualified Leads", "CAC", "LTV", "Demo Bookings", "Conversion Rate"],
    creative_angles=[
        "Before/after efficiency gains",
        "Industry benchmarks and competitive advantage",
        "Technical depth + business value",
        "Customer success stories and case studies",
        "Webinar-style educational content",
    ],
    common_objections=[
        "Too expensive/high cost",
        "Integration complexity",
        "Switching costs from existing solution",
        "Security and compliance concerns",
        "Long implementation timeline",
    ],
    default_tone="Professional, consultative, data-driven",
)

# eCommerce/D2C Preset
ECOM_D2C = IndustryPreset(
    name="eCommerce/D2C",
    description="Direct-to-consumer product brands selling online",
    strategy_notes=[
        "Focus on ROAS and repeat customer value",
        "Create urgency and scarcity",
        "User-generated content is highly effective",
        "Mobile-first creative required",
        "Seasonal and trend-based campaigns work well",
    ],
    priority_channels=["Instagram Reels", "TikTok", "Pinterest", "Meta Ads", "Email"],
    sample_kpis=["ROAS", "AOV", "Repeat Purchase Rate", "CAC", "Conversion Rate"],
    creative_angles=[
        "Lifestyle and aspiration",
        "Product in action and real-world use",
        "Customer testimonials and unboxing",
        "Limited-time offers and exclusivity",
        "Trend-jacking and cultural relevance",
    ],
    common_objections=[
        "I can get it cheaper elsewhere",
        "Quality concerns from unfamiliar brand",
        "Shipping costs too high",
        "Return policy uncertainty",
        "Similar products from bigger brands",
    ],
    default_tone="Trendy, energetic, relatable, FOMO-inducing",
)

# Local Service Preset
LOCAL_SERVICE = IndustryPreset(
    name="Local Service",
    description="Services that operate in specific geographic areas (plumbing, beauty, fitness, etc.)",
    strategy_notes=[
        "Focus on local visibility and foot traffic",
        "Reviews and social proof are critical",
        "Community engagement and word-of-mouth",
        "Mobile users searching 'near me'",
        "Seasonal promotions and local events",
    ],
    priority_channels=["Instagram", "Google Maps", "WhatsApp", "Local Facebook", "SMS"],
    sample_kpis=["Foot Traffic", "Bookings", "Review Count", "Star Rating", "Repeat Customers"],
    creative_angles=[
        "Before/after transformations",
        "Local community and team spotlight",
        "Customer reviews and testimonials",
        "Limited-time local promotions",
        "Behind-the-scenes and process transparency",
    ],
    common_objections=[
        "I don't know you or haven't heard of you",
        "Competitor is closer/more convenient",
        "Pricing is too high vs competitors",
        "Bad past experience with similar service",
        "Lack of reviews or social proof",
    ],
    default_tone="Friendly, trustworthy, community-focused, approachable",
)

# Coaching/Personal Brand Preset
COACHING = IndustryPreset(
    name="Coaching",
    description="Personal brands, coaches, consultants, and thought leaders",
    strategy_notes=[
        "Focus on authority, transformation, and personal connection",
        "Content is the primary product",
        "Community and audience loyalty matter most",
        "Long-form content drives credibility",
        "Webinars and masterclasses are conversion tools",
    ],
    priority_channels=["YouTube", "Webinars", "Email", "Instagram", "LinkedIn"],
    sample_kpis=[
        "Email Subscribers",
        "Course Sales",
        "Coaching Clients",
        "Engagement Rate",
        "Transformation Stories",
    ],
    creative_angles=[
        "Personal journey and transformation story",
        "Expert insights and industry secrets",
        "Success stories of students/clients",
        "Problem-solution frameworks",
        "Free value delivery and education",
    ],
    common_objections=[
        "I can find this information free online",
        "Skeptical about whether you can actually help",
        "Too expensive for coaching/course",
        "Worried it won't work for my situation",
        "Don't have time to implement",
    ],
    default_tone="Inspirational, authentic, educational, empathetic",
)

# Dictionary for easy lookup
INDUSTRY_PRESETS = {
    "b2b_saas": B2B_SAAS,
    "ecom_d2c": ECOM_D2C,
    "local_service": LOCAL_SERVICE,
    "coaching": COACHING,
}


def get_industry_preset(industry_key: str) -> IndustryPreset | None:
    """Get an industry preset by key.

    Args:
        industry_key: Key like 'b2b_saas', 'ecom_d2c', 'local_service', 'coaching'

    Returns:
        IndustryPreset or None if not found
    """
    return INDUSTRY_PRESETS.get(industry_key.lower() if industry_key else None)


def list_available_industries() -> List[str]:
    """List all available industry preset keys."""
    return list(INDUSTRY_PRESETS.keys())
