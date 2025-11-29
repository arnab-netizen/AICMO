"""
Industry-Specific Configuration for AICMO

Maps industries to appropriate personas, channels, and messaging styles.

FIX #4: Ensures personas and channels are tailored to industry, not generic.
"""

from typing import TypedDict, List, Dict, Optional


class IndustryChannelConfig(TypedDict):
    """Configuration for channels specific to an industry."""

    primary: str  # Main channel (e.g., "Instagram")
    secondary: List[str]  # Supporting channels
    tertiary: List[str]  # Tertiary channels
    avoid: List[str]  # Channels to avoid
    reasoning: str  # Why these channels work for this industry


class IndustryPersonaConfig(TypedDict):
    """Default persona template for an industry."""

    name: str
    role: str
    age_range: str
    primary_pain_points: List[str]
    primary_goals: List[str]
    decision_factors: List[str]
    channel_preference: str


class IndustryConfig(TypedDict):
    """Complete configuration for an industry."""

    industry_key: str
    display_name: str
    channels: IndustryChannelConfig
    default_personas: List[IndustryPersonaConfig]
    messaging_tone: str
    content_formats: List[str]


# Comprehensive industry configurations
INDUSTRY_CONFIGS: Dict[str, IndustryConfig] = {
    # ============================================================
    # Food & Beverage
    # ============================================================
    "food_beverage": {
        "industry_key": "food_beverage",
        "display_name": "Food & Beverage",
        "channels": {
            "primary": "Instagram",
            "secondary": ["TikTok", "Facebook"],
            "tertiary": ["Pinterest", "YouTube"],
            "avoid": ["LinkedIn", "Email-heavy"],
            "reasoning": "Visual content, trends, user-generated content drive F&B discovery",
        },
        "default_personas": [
            {
                "name": "Instagram-Savvy Foodie",
                "role": "Content Creator / Influencer",
                "age_range": "18-35",
                "primary_pain_points": [
                    "Finding Instagrammable food experiences",
                    "Staying on top of trends",
                    "Authentic dining stories to share",
                ],
                "primary_goals": [
                    "Discover new places to eat and photograph",
                    "Build personal brand/following",
                    "Have memorable experiences to share",
                ],
                "decision_factors": [
                    "Visual appeal",
                    "Trending/unique concept",
                    "Photo opportunities",
                    "Peer reviews and tags",
                ],
                "channel_preference": "Instagram",
            },
            {
                "name": "Local Community Regular",
                "role": "Neighborhood Regular",
                "age_range": "25-55",
                "primary_pain_points": [
                    "Finding reliable quality food",
                    "Supporting local businesses",
                    "Value for money",
                ],
                "primary_goals": [
                    "Discover new local spots",
                    "Save money on dining",
                    "Support local community",
                ],
                "decision_factors": [
                    "Word-of-mouth recommendations",
                    "Local reputation",
                    "Consistent quality",
                    "Fair pricing",
                ],
                "channel_preference": "Facebook",
            },
        ],
        "messaging_tone": "Visual, trendy, community-focused, experiential",
        "content_formats": [
            "Reels",
            "Carousels",
            "Stories",
            "User-generated content",
            "Behind-the-scenes",
        ],
    },
    # ============================================================
    # Boutique Retail / Fashion
    # ============================================================
    "boutique_retail": {
        "industry_key": "boutique_retail",
        "display_name": "Boutique Retail & Fashion",
        "channels": {
            "primary": "Instagram",
            "secondary": ["Pinterest", "TikTok"],
            "tertiary": ["YouTube", "Facebook"],
            "avoid": ["LinkedIn"],
            "reasoning": "Visual product showcase, style inspiration, community engagement",
        },
        "default_personas": [
            {
                "name": "Fashion-Forward Shopper",
                "role": "Style Influencer",
                "age_range": "20-40",
                "primary_pain_points": [
                    "Finding unique, trendy pieces",
                    "Discovering emerging brands",
                    "Staying fashionable without overspending",
                ],
                "primary_goals": [
                    "Express personal style",
                    "Find unique pieces",
                    "Discover new brands",
                ],
                "decision_factors": [
                    "Brand uniqueness",
                    "Aesthetic appeal",
                    "Quality-to-price ratio",
                    "Social proof/influencer endorsement",
                ],
                "channel_preference": "Instagram",
            },
            {
                "name": "Conscious Consumer",
                "role": "Ethical Shopper",
                "age_range": "25-55",
                "primary_pain_points": [
                    "Finding sustainable brands",
                    "Supporting ethical businesses",
                    "Quality and longevity",
                ],
                "primary_goals": [
                    "Shop sustainably",
                    "Support small businesses",
                    "Find quality pieces that last",
                ],
                "decision_factors": [
                    "Brand values/ethics",
                    "Sustainability credentials",
                    "Quality and durability",
                    "Local/community connection",
                ],
                "channel_preference": "Instagram",
            },
        ],
        "messaging_tone": "Aspirational, trendy, community-conscious, aesthetic",
        "content_formats": [
            "Product showcase",
            "Style guides",
            "Behind-the-scenes",
            "User-generated content",
            "Lookbooks",
        ],
    },
    # ============================================================
    # SaaS / B2B Software
    # ============================================================
    "saas": {
        "industry_key": "saas",
        "display_name": "SaaS & B2B Software",
        "channels": {
            "primary": "LinkedIn",
            "secondary": ["Email", "YouTube"],
            "tertiary": ["Twitter/X", "Slack communities"],
            "avoid": ["TikTok", "Instagram"],
            "reasoning": "Professional decision-makers, thought leadership, ROI-focused messaging",
        },
        "default_personas": [
            {
                "name": "VP of Operations",
                "role": "Decision Maker",
                "age_range": "35-55",
                "primary_pain_points": [
                    "Operational efficiency",
                    "Team productivity",
                    "ROI measurement",
                    "Implementation complexity",
                ],
                "primary_goals": [
                    "Reduce operational costs",
                    "Improve team efficiency",
                    "Measure and prove ROI",
                    "Reduce tech stack complexity",
                ],
                "decision_factors": [
                    "Measurable ROI",
                    "Ease of integration",
                    "Vendor reliability",
                    "Security and compliance",
                    "Total cost of ownership",
                ],
                "channel_preference": "LinkedIn",
            },
            {
                "name": "Technical Implementer",
                "role": "IC / Team Lead",
                "age_range": "25-40",
                "primary_pain_points": [
                    "Technical integration complexity",
                    "Learning curve",
                    "Support availability",
                    "API reliability",
                ],
                "primary_goals": [
                    "Easy implementation",
                    "Strong API documentation",
                    "Quick time-to-value",
                    "Great developer support",
                ],
                "decision_factors": [
                    "Technical documentation",
                    "API quality",
                    "Community support",
                    "Developer experience",
                    "Customization options",
                ],
                "channel_preference": "Email",
            },
        ],
        "messaging_tone": "Professional, ROI-focused, thought leadership, problem-solution",
        "content_formats": [
            "Case studies",
            "Webinars",
            "White papers",
            "Product demos",
            "ROI calculators",
        ],
    },
    # ============================================================
    # Fitness & Wellness
    # ============================================================
    "fitness": {
        "industry_key": "fitness",
        "display_name": "Fitness & Wellness",
        "channels": {
            "primary": "Instagram",
            "secondary": ["TikTok", "YouTube"],
            "tertiary": ["Pinterest", "Facebook"],
            "avoid": ["LinkedIn"],
            "reasoning": "Inspiration, transformation stories, community motivation, visual progress",
        },
        "default_personas": [
            {
                "name": "Fitness Enthusiast",
                "role": "Regular / Content Creator",
                "age_range": "18-35",
                "primary_pain_points": [
                    "Staying motivated",
                    "Finding effective workouts",
                    "Tracking progress",
                    "Avoiding injury",
                ],
                "primary_goals": [
                    "Build muscle / lose fat",
                    "Maintain consistency",
                    "See results",
                    "Stay inspired by community",
                ],
                "decision_factors": [
                    "Transformation stories",
                    "Expert credibility",
                    "Community support",
                    "Program variety",
                    "Tangible results",
                ],
                "channel_preference": "Instagram",
            },
            {
                "name": "Wellness Seeker",
                "role": "New to Fitness",
                "age_range": "30-60",
                "primary_pain_points": [
                    "Starting from scratch",
                    "Time constraints",
                    "Low confidence",
                    "Intimidating gym environment",
                ],
                "primary_goals": [
                    "Improve health",
                    "Increase energy",
                    "Build confidence",
                    "Find supportive community",
                ],
                "decision_factors": [
                    "Beginner-friendly approach",
                    "Supportive community",
                    "No judgment",
                    "Flexible scheduling",
                    "Easy-to-follow guidance",
                ],
                "channel_preference": "YouTube",
            },
        ],
        "messaging_tone": "Motivational, transformational, community-driven, results-focused",
        "content_formats": [
            "Transformation stories",
            "Workout tips",
            "Nutrition guides",
            "Community challenges",
            "Motivational quotes",
        ],
    },
    # ============================================================
    # E-Commerce / Online Retail
    # ============================================================
    "ecommerce": {
        "industry_key": "ecommerce",
        "display_name": "E-Commerce & Online Retail",
        "channels": {
            "primary": "Instagram",
            "secondary": ["Pinterest", "Email"],
            "tertiary": ["TikTok", "YouTube"],
            "avoid": ["LinkedIn"],
            "reasoning": "Visual discovery, inspiration, product showcase, retargeting",
        },
        "default_personas": [
            {
                "name": "Social Shopper",
                "role": "Online Browser",
                "age_range": "18-40",
                "primary_pain_points": [
                    "Finding new products to try",
                    "Discovering quality brands",
                    "Avoiding bad purchases",
                    "Shipping delays",
                ],
                "primary_goals": [
                    "Discover trending products",
                    "Find good deals",
                    "Quick checkout",
                    "Reliable delivery",
                ],
                "decision_factors": [
                    "Influencer recommendations",
                    "User reviews",
                    "Price and shipping",
                    "Brand aesthetics",
                    "Return policy",
                ],
                "channel_preference": "Instagram",
            },
            {
                "name": "Deal Hunter",
                "role": "Price Conscious Buyer",
                "age_range": "25-60",
                "primary_pain_points": [
                    "Finding best prices",
                    "Missing out on sales",
                    "Unexpected costs",
                    "Trust in online sellers",
                ],
                "primary_goals": [
                    "Save money",
                    "Find deals and discounts",
                    "Shop smart",
                    "Avoid scams",
                ],
                "decision_factors": [
                    "Price comparison",
                    "Discount codes",
                    "Free shipping",
                    "Clear return policy",
                    "Verified reviews",
                ],
                "channel_preference": "Email",
            },
        ],
        "messaging_tone": "Deal-focused, trendy, trust-building, convenience-oriented",
        "content_formats": [
            "Product showcases",
            "Customer reviews",
            "Behind-the-scenes",
            "Flash sales alerts",
            "Style guides",
        ],
    },
}


def get_industry_config(industry_keyword: Optional[str]) -> Optional[IndustryConfig]:
    """
    Get industry configuration by keyword (case-insensitive partial match).

    Args:
        industry_keyword: Industry name or keyword (e.g., "SaaS", "food", "instagram")

    Returns:
        IndustryConfig if match found, None otherwise
    """
    if not industry_keyword:
        return None

    keyword_lower = industry_keyword.lower().strip()

    # Exact key match
    if keyword_lower in INDUSTRY_CONFIGS:
        return INDUSTRY_CONFIGS[keyword_lower]

    # Partial match in display names
    for config in INDUSTRY_CONFIGS.values():
        if keyword_lower in config["display_name"].lower():
            return config

    # Keyword matching
    for config in INDUSTRY_CONFIGS.values():
        if keyword_lower in config["industry_key"].lower():
            return config

    return None


def get_primary_channel_for_industry(industry_keyword: Optional[str]) -> Optional[str]:
    """
    Get the primary recommended channel for an industry.

    Args:
        industry_keyword: Industry name/keyword

    Returns:
        Primary channel name (e.g., "Instagram") or None
    """
    config = get_industry_config(industry_keyword)
    if config:
        return config["channels"]["primary"]
    return None


def get_default_personas_for_industry(
    industry_keyword: Optional[str],
) -> List[IndustryPersonaConfig]:
    """
    Get default personas for an industry.

    Args:
        industry_keyword: Industry name/keyword

    Returns:
        List of default personas or empty list
    """
    config = get_industry_config(industry_keyword)
    if config:
        return config["default_personas"]
    return []


def convert_industry_persona_to_persona_card(
    persona_config: IndustryPersonaConfig,
) -> "PersonaCard":  # noqa: F821
    """
    Convert IndustryPersonaConfig to PersonaCard model for output.

    Args:
        persona_config: Industry-specific persona template

    Returns:
        PersonaCard with all required fields populated
    """
    from aicmo.io.client_reports import PersonaCard

    # Build demographics from role and age_range
    demographics = f"{persona_config.get('role', 'Professional')}, {persona_config.get('age_range', '25-45')}"

    # Build psychographics from decision factors and goals
    decision_factors = persona_config.get("decision_factors", [])
    primary_goals = persona_config.get("primary_goals", [])
    psychographics_items = decision_factors[:2] if decision_factors else []
    if primary_goals and len(psychographics_items) < 2:
        psychographics_items.extend(primary_goals[: 2 - len(psychographics_items)])
    psychographics = "; ".join(psychographics_items) if psychographics_items else "Results-oriented, quality-focused"

    return PersonaCard(
        name=persona_config.get("name", "Default Persona"),
        demographics=demographics,
        psychographics=psychographics,
        pain_points=persona_config.get("primary_pain_points", []),
        triggers=[],  # Not provided in industry config, using empty
        objections=[],  # Not provided in industry config, using empty
        content_preferences=[],  # Not provided in industry config, using empty
        primary_platforms=[persona_config.get("channel_preference", "LinkedIn")],
        tone_preference="Professional",
    )
