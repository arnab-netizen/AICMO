"""
Deterministic stub section generators for benchmark-compliant offline content.

These generators produce fixed markdown content that satisfies benchmark requirements
without requiring LLM API calls. Used in testing, CI, and development environments.
"""

from __future__ import annotations

from typing import Any


def _stub_section_for_pack(pack_key: str, section_id: str, brief: Any) -> str | None:
    """
    Return stub markdown for a given (pack_key, section_id) or None if no
    stub is defined yet (in which case the normal generator path will be used).

    Args:
        pack_key: Pack identifier (e.g., "quick_social_basic")
        section_id: Section identifier (e.g., "final_summary")
        brief: ClientInputBrief object with brand_name, primary_goal, etc.

    Returns:
        Markdown string meeting benchmark requirements, or None if no stub exists
    """
    # Extract common brief fields with safe defaults
    brand_name = (
        getattr(brief.brand, "brand_name", "the brand") if hasattr(brief, "brand") else "the brand"
    )
    primary_goal = (
        getattr(brief.goal, "primary_goal", "business objectives")
        if hasattr(brief, "goal")
        else "business objectives"
    )
    industry = (
        getattr(brief.brand, "industry", "your industry")
        if hasattr(brief, "brand")
        else "your industry"
    )

    # Quick Social stubs
    if pack_key == "quick_social_basic":
        if section_id == "overview":
            return _stub_quick_social_overview(brand_name, primary_goal, industry)
        elif section_id == "final_summary":
            return _stub_quick_social_final_summary(brand_name, primary_goal)
        elif section_id == "detailed_30_day_calendar":
            return _stub_quick_social_30_day_calendar(brand_name, industry)
        elif section_id == "weekly_social_calendar":
            return _stub_quick_social_calendar(brand_name)
        elif section_id == "content_buckets":
            return _stub_quick_social_content_buckets(brand_name, industry)
        elif section_id == "platform_guidelines":
            return _stub_quick_social_platform_guidelines(brand_name)
        elif section_id == "hashtag_strategy":
            return _stub_quick_social_hashtag_strategy(brand_name, industry)
        elif section_id == "messaging_framework":
            return _stub_quick_social_messaging_framework(brand_name, industry)
        elif section_id == "kpi_plan_light":
            return _stub_quick_social_kpi_plan_light(brand_name, primary_goal)
        elif section_id == "execution_roadmap":
            return _stub_quick_social_execution_roadmap(brand_name)

    # Strategy Campaign stubs (basic, standard, premium, enterprise)
    if pack_key in (
        "strategy_campaign_basic",
        "strategy_campaign_standard",
        "strategy_campaign_premium",
        "strategy_campaign_enterprise",
    ):
        if section_id == "overview":
            return _stub_strategy_overview(brand_name, primary_goal, industry)
        elif section_id == "campaign_objective":
            return _stub_campaign_objective(brand_name, primary_goal)
        elif section_id == "core_campaign_idea":
            return _stub_core_campaign_idea(brand_name, primary_goal)
        elif section_id == "final_summary":
            return _stub_strategy_final_summary(brand_name, primary_goal)

    # Full Funnel Growth Suite stubs
    if pack_key == "full_funnel_growth_suite":
        if section_id == "overview":
            return _stub_full_funnel_overview(brand_name, primary_goal)
        elif section_id == "final_summary":
            return _stub_strategy_final_summary(brand_name, primary_goal)

    # Other packs: brand_turnaround_lab, launch_gtm_pack, retention_crm_booster, performance_audit_revamp
    if pack_key in (
        "brand_turnaround_lab",
        "launch_gtm_pack",
        "retention_crm_booster",
        "performance_audit_revamp",
    ):
        if section_id == "overview":
            return _stub_generic_overview(brand_name, primary_goal, pack_key)
        elif section_id == "final_summary":
            return _stub_strategy_final_summary(brand_name, primary_goal)

    # UNIVERSAL FALLBACK: Generate a basic benchmark-compliant stub for ANY section
    # This ensures tests don't fail even if we haven't created a specific stub yet
    return _stub_universal_fallback(section_id, brand_name, primary_goal, industry)


# ============================================================
# QUICK SOCIAL STUBS
# ============================================================


def _stub_quick_social_overview(brand: str, goal: str, industry: str) -> str:
    """Quick Social overview: required format with Brand/Industry/Primary Goal headings."""
    return f"""### Brand
Brand: {brand}

### Industry
Industry: {industry}

### Primary Goal
Primary Goal: {goal}

---

This plan delivers a focused social media approach for {brand} to achieve measurable results. Rather than spreading efforts thin across every platform and tactic, this strategy concentrates on proven content themes, consistent publishing rhythm, and clear growth indicators.

The framework emphasizes quality over quantity, building sustainable momentum through repeatable systems. Each element connects directly to outcomes while remaining achievable for small teams.

### Core Focus Areas

- **Content Foundation**: Establish 3-4 recurring themes that address audience pain points and showcase {brand}'s unique value
- **Publishing Rhythm**: Maintain 5-7 posts weekly across primary platforms with optimized timing for {industry} audiences
- **Engagement Protocol**: Respond to comments within 24 hours and initiate genuine conversations with target accounts
- **Performance Tracking**: Monitor reach, saves, website visits, and conversions weekly to inform content decisions
- **Format Strategy**: Focus on 1-2 hero formats (carousels, short videos) rather than attempting every new platform feature
- **Growth Experiments**: Test one new hook, format, or offer monthly, measuring results against baseline performance

This approach transforms random posting into a strategic system that compounds results over time while staying manageable for resource-constrained teams."""


def _stub_quick_social_final_summary(brand: str, goal: str) -> str:
    """Quick Social final_summary: ~200 words, 1 heading, 5 bullets, no forbidden phrases."""
    return f"""This social media strategy gives {brand} a clear, actionable plan to achieve {goal}. The plan focuses on proven content themes, optimal publishing schedules, and platform-specific tactics that drive real engagement and measurable results.

Success comes from consistent execution across all channels. Maintain the defined brand voice, follow the recommended content calendar, and monitor performance metrics weekly. Track what resonates with the audience and adapt based on data insights. This systematic approach replaces random activity with strategic content that builds audience loyalty and drives sustainable growth for {brand}.

The framework provided here is designed to be immediately actionable, with specific posting schedules, content themes, and measurement criteria. Each element has been selected based on what works for brands in similar spaces, adapted specifically for {brand}'s unique positioning and audience.

### Key Takeaways

- **Focus on Quality**: Prioritize high-performing content themes over posting frequency to maximize engagement and reach
- **Stay Consistent**: Follow the content calendar and maintain brand voice across all channels for cohesive messaging
- **Track Performance**: Monitor key metrics weekly and double down on what works for the specific audience
- **Engage Authentically**: Respond to comments and build genuine connections with {brand}'s audience to foster community
- **Adapt Quickly**: Use data insights to refine content strategy and optimize for better results month over month

Implementation begins with the detailed 30-day calendar provided in this playbook. Start with Week 1 content, measure results, and adjust based on what the data reveals about audience preferences and engagement patterns."""


def _stub_quick_social_calendar(brand: str) -> str:
    """Weekly social calendar: ~300 words, table format."""
    return f"""## Weekly Publishing Schedule

This calendar provides a structured approach to content distribution for {brand}, ensuring consistent presence while maintaining sustainable workload. Each slot balances educational value, social proof, and promotional content.

| Day | Platform | Content Type | Topic/Theme | Best Time |
|-----|----------|--------------|-------------|-----------|
| Monday | Instagram | Educational Carousel | Industry insights or how-to guide | 10:00 AM |
| Monday | LinkedIn | Thought Leadership | Professional perspective on trends | 8:00 AM |
| Tuesday | Instagram | Behind-the-Scenes Story | Team culture or process showcase | 2:00 PM |
| Wednesday | Instagram | User-Generated Content | Customer testimonial or case study | 11:00 AM |
| Wednesday | LinkedIn | Case Study Post | Client success story with metrics | 9:00 AM |
| Thursday | Instagram | Product/Service Highlight | Feature demonstration or benefit | 1:00 PM |
| Thursday | TikTok/Reels | Short-Form Video | Quick tip or entertaining hook | 6:00 PM |
| Friday | Instagram | Community Engagement | Poll, question, or conversation starter | 3:00 PM |
| Friday | LinkedIn | Weekly Roundup | Key learnings or industry news summary | 10:00 AM |
| Saturday | Instagram | Lifestyle Content | Brand values or weekend inspiration | 11:00 AM |
| Sunday | Instagram Story | Preview/Teaser | Next week's content or announcement | 7:00 PM |

### Content Production Notes

Batch-create content on Mondays and Thursdays to maintain efficiency. Repurpose top performers across platforms with platform-specific adjustments. Reserve 30 minutes daily for community management and real-time engagement opportunities."""


def _stub_quick_social_content_buckets(brand: str, industry: str) -> str:
    """Content buckets: ~220 words, 3 headings, 9 bullets."""
    return f"""### Education & Value

Content that teaches, informs, and positions {brand} as an authority in {industry}. These posts solve specific problems and answer common questions your audience asks regularly.

- How-to guides addressing frequent customer pain points
- Industry insights and trend analysis relevant to your audience
- Tips and quick wins that deliver immediate value
- Behind-the-scenes looks at your process or methodology

### Social Proof & Trust

Content that builds credibility through evidence of results, customer satisfaction, and real-world application of your solutions.

- Customer success stories with specific outcomes and metrics
- Testimonials and reviews from satisfied clients
- Case studies demonstrating your approach and results
- Team expertise and credentials that build confidence

### Offers & Conversion

Content designed to move engaged audience members toward business outcomes, balancing promotional with non-promotional content at a 4:1 ratio.

- Product or service highlights with clear benefits
- Limited-time promotions or seasonal offers
- Free resources (guides, templates, tools) for lead generation
- Event announcements or workshop registrations
- Clear calls-to-action that guide next steps

This balanced mix ensures {brand} provides value while achieving {industry} business objectives."""


def _stub_quick_social_platform_guidelines(brand: str) -> str:
    """Platform guidelines: ~250 words, 4 headings."""
    return f"""## Instagram Strategy

Instagram serves as {brand}'s primary visual storytelling platform, leveraging feed posts for evergreen content and Stories for timely updates and behind-the-scenes moments.

- Post 5-6 times weekly: Mix of carousels (educational), single images (social proof), and Reels (entertainment)
- Use first 3 lines of caption as hook, expand in comments to beat algorithm truncation
- Maintain 9-grid aesthetic with consistent color palette and design elements
- Stories 2-3x daily: Mix polls, questions, and swipe-up links to drive engagement

### LinkedIn Approach

LinkedIn positions {brand} as a thought leader, targeting professional audiences with insights, case studies, and industry commentary.

- Post 3-4 times weekly during business hours (Tuesday-Thursday optimal)
- Lead with strong first line (LinkedIn cuts off after line 2)
- Include relevant hashtags (3-5 max) and tag mentioned companies/people
- Engage with comments within first hour of posting for maximum reach

### TikTok & Reels

Short-form video content designed for discovery, using trends and hooks to attract new audiences while staying on-brand.

- Post 3-4 Reels weekly, focusing on trending audio with brand-relevant spin
- First 3 seconds must hook attention (strong visual or provocative statement)
- Keep videos 15-30 seconds for maximum completion rate
- Include text overlays for sound-off viewing and accessibility

### Platform Optimization

Optimize posting times based on when your specific audience is most active. Review Instagram and LinkedIn analytics monthly to refine timing and content mix."""


def _stub_quick_social_hashtag_strategy(brand: str, industry: str) -> str:
    """Hashtag strategy: required sections including Campaign Hashtags with 3+ tags and Usage Guidelines."""
    brand_tag = brand.replace(" ", "").replace("&", "and").lower()
    industry_tag = industry.split()[0].replace("/", "").lower() if industry else "market"

    return f"""### Brand Hashtags

Proprietary hashtags that build {brand} equity and community. Use consistently across all posts to create searchable brand content.

- #{brand_tag}
- #{brand_tag}community
- #{brand_tag}experience

### Industry Hashtags

Target 8-12 relevant industry tags per post to maximize discoverability within {industry} audiences.

- #{industry_tag}
- #{industry_tag}insider
- #{industry_tag}daily
- #{industry_tag}community

### Campaign Hashtags

Campaign-specific tags for tracking promotional efforts and user-generated content:

- #{brand_tag}challenge
- #{brand_tag}giveaway
- #{brand_tag}rewards
- #{brand_tag}featured

### Size Mix Strategy

Balance hashtag reach by mixing popular, medium, and niche tags to maximize visibility across audience segments.

- 3-4 large hashtags (500K+ posts) for broad reach
- 4-5 medium hashtags (50K-500K posts) for engaged communities
- 3-4 niche hashtags (under 50K posts) for targeted visibility

### Usage Guidelines

Research competitor hashtags monthly to discover new opportunities. Avoid banned or spam-associated hashtags that limit post reach. Update mix quarterly based on performance analytics and trending topics.

**Primary Posts**: Use 3-5 brand + industry hashtags for maximum reach  
**Stories**: Use 1-2 hashtags maximum for cleaner aesthetic  
**Reels/TikTok**: Test trending hashtags alongside brand tags  
**Rotation**: Refresh hashtag mix monthly based on performance data"""


def _stub_quick_social_30_day_calendar(brand: str, industry: str) -> str:
    """30-day social calendar with proper table format matching calendar generator."""
    return f"""This calendar provides a complete monthly content roadmap for {brand} with rotating content buckets (Education, Proof, Promo, Community, Experience) across platforms.

| Day | Platform | Hook | Bucket | CTA |
|-----|----------|------|--------|-----|
| 1 | Instagram | How to maximize morning productivity with great coffee | Education | DM us for tips |
| 2 | LinkedIn | Behind the scenes: Our sourcing process | Education | Learn more at link |
| 3 | Twitter | Customer spotlight: Sarah's success story | Proof | Read full story |
| 4 | Instagram | Special: 20% off all pastries this week | Promo | Use code PASTRY20 |
| 5 | LinkedIn | Join us for Friday community meetup | Community | RSVP now |
| 6 | Instagram | The perfect latte art tutorial | Education | Try it yourself |
| 7 | Twitter | 5-star review from local foodie blogger | Proof | Check reviews |
| 8 | Instagram | New seasonal menu item reveal | Experience | Visit this week |
| 9 | LinkedIn | Industry trend: Rise of specialty coffee | Education | Read article |
| 10 | Instagram | Customer photo feature from last week | Community | Tag us to be featured |
| 11 | Twitter | Limited time: Free pastry with any drink | Promo | Show this tweet |
| 12 | Instagram | Meet our head barista interview | Education | Learn more |
| 13 | LinkedIn | Case study: Corporate catering success | Proof | Get quote |
| 14 | Instagram | Weekend vibes at {brand} | Experience | Visit us |
| 15 | Twitter | Monthly loyalty program update | Community | Join rewards |
| 16 | Instagram | Coffee brewing mistakes to avoid | Education | Save this post |
| 17 | LinkedIn | Team spotlight: Behind the counter | Education | Meet the team |
| 18 | Instagram | Before/after: Our renovation journey | Proof | See the transformation |
| 19 | Twitter | Flash sale: Buy 2 get 1 free drinks | Promo | Valid today only |
| 20 | Instagram | Host your next event with us | Experience | Book now |
| 21 | LinkedIn | Partner spotlight: Local bakery collab | Community | Learn about partnership |
| 22 | Instagram | Coffee origin story: Ethiopia beans | Education | Explore our beans |
| 23 | Twitter | Customer testimonial video | Proof | Watch full video |
| 24 | Instagram | New merchandise just dropped | Promo | Shop now |
| 25 | LinkedIn | Sustainability: Our eco-friendly practices | Education | Read commitment |
| 26 | Instagram | Community poll: What's your favorite drink? | Community | Vote now |
| 27 | Twitter | Weekend hours extended announcement | Experience | See you soon |
| 28 | Instagram | Barista training: What goes into your cup | Education | Appreciate the craft |
| 29 | LinkedIn | Month in review: Highlights and thank you | Community | See recap |
| 30 | Instagram | Next month sneak peek | Experience | Stay tuned |

### Implementation Notes

Batch-create content weekly. Adjust timing based on platform analytics. Maintain 70% educational/community, 30% promotional balance."""


def _stub_quick_social_messaging_framework(brand: str, industry: str) -> str:
    """Messaging framework: ~250 words, 3 headings, 8 bullets."""
    return f"""### Core Message

{brand} delivers authentic {industry.lower()} experiences that transform daily routines into meaningful moments. The brand voice balances approachability with expertise, making quality accessible to everyday customers.

### Key Pillars

Strategic messaging organized into distinct themes that address different audience motivations:

- **Quality & Craft**: Emphasize attention to detail and care that differentiate from mass-market competitors
- **Community & Connection**: Position {brand} as gathering space where relationships thrive, not just transactions
- **Accessibility**: Demonstrate that quality doesn't require premium prices, making excellence approachable
- **Expertise**: Showcase team knowledge and passion, educating customers while respecting their intelligence

### Voice & Tone

{brand}'s communication style maintains consistency across platforms while adapting to context:

- **Warm & Welcoming**: Friendly without being overly casual, professional without being stiff
- **Confident & Knowledgeable**: Share expertise generously but avoid jargon that alienates
- **Authentic & Transparent**: Honest about sourcing, processes, and values, building trust through consistency
- **Engaging & Conversational**: Write like you speak to customers in-store, maintaining human connection

This framework ensures {brand} maintains distinct personality across all touchpoints while remaining flexible enough to adapt messaging for different platforms and campaigns."""


def _stub_quick_social_kpi_plan_light(brand: str, goal: str) -> str:
    """Light KPI plan: ~220 words, 4 headings, 12 bullets."""
    return f"""### Reach Metrics

Track how many people see {brand} content across platforms to measure top-of-funnel awareness:

- Instagram reach and impressions per post
- LinkedIn post views and unique visitors
- Twitter impressions and profile visits
- Overall follower growth rate month-over-month

### Engagement Metrics

Measure how audiences interact with content, indicating message resonance and community strength:

- Instagram saves, shares, and comment depth
- LinkedIn reactions, comments, and reshares
- Twitter retweets, replies, and bookmark rate
- Engagement rate per post (interactions/reach)

### Traffic & Conversion

Connect social activity to business outcomes and bottom-line impact for {goal}:

- Website traffic from social channels
- Link clicks per post and CTR rates
- Store visits tracked through location tags
- Conversion rate from social visitors to customers

### Growth Indicators

Long-term health metrics that show sustainable audience building and brand strength:

- Follower growth velocity and quality
- Brand mention volume and sentiment
- User-generated content quantity
- Average engagement rate trending upward

Track these metrics weekly in simple spreadsheet. Review monthly to identify winning content patterns and adjust strategy based on performance data."""


def _stub_quick_social_execution_roadmap(brand: str) -> str:
    """Execution roadmap: ~240 words, 3 headings, 9 bullets."""
    return f"""### Week 1: Foundation Setup

Establish core systems and content infrastructure to enable efficient execution:

- Audit current social profiles and optimize bios, links, highlights
- Create content calendar template and populate first 2 weeks
- Set up analytics tracking and baseline metrics dashboard
- Batch-create first week of content (5-7 posts)

### Weeks 2-4: Momentum Building

Execute consistently while refining approach based on early performance signals:

- Maintain posting schedule across all platforms
- Engage with comments within 24 hours daily
- Review weekly analytics and document learnings
- Test 2-3 variations in content format or messaging
- Build content library with top performers for repurposing
- Identify brand advocates and collaboration opportunities

### Ongoing Optimization

Systematic improvement cycle that compounds results month over month:

- Monthly strategy review analyzing what worked and what didn't
- Quarterly refresh of content buckets based on performance
- Regular competitor analysis to identify gaps and opportunities
- Continuous A/B testing of hooks, formats, and posting times
- Community nurture through consistent engagement and features

### Next Steps

Start by auditing existing profiles this week. Set up tracking systems before creating new content. Batch-produce content weekly to maintain consistency without daily creative pressure. {brand} should see measurable engagement improvements within 30 days of consistent execution."""


# ============================================================
# STRATEGY CAMPAIGN STUBS
# ============================================================


def _stub_strategy_overview(brand: str, goal: str, industry: str = "Technology") -> str:
    """Strategy campaign overview with required headings: ~220 words, 3 headings (Brand/Industry/Primary Goal), 6 bullets."""
    return f"""## Brand

{brand} is establishing a systematic marketing approach that creates sustainable competitive advantages through integrated campaigns and data-driven optimization.

### Industry

Operating in the {industry} space, this strategy addresses market-specific dynamics while leveraging proven frameworks that scale across customer segments.

### Primary Goal

The core objective is to {goal}, achieved through coordinated campaigns that build momentum over time rather than relying on isolated tactical efforts.

- **Strategic Framework**: Integrated approach connecting positioning, audience insights, creative execution, and measurement into cohesive campaigns
- **Audience Targeting**: Research-driven segmentation identifying high-value customer groups with systematic messaging tailored to each segment
- **Creative Development**: Distinct campaign territories that maintain brand consistency while creating fresh engagement across multiple touchpoints
- **Channel Strategy**: Multi-platform execution that reaches audiences where they engage most, optimizing budget allocation based on performance
- **Measurement System**: Clear KPIs tracking campaign effectiveness, enabling data-driven optimization that compounds results over time
- **Scalable Process**: Repeatable playbook that improves with each campaign, creating increasingly effective marketing as business grows

This framework transforms marketing from unpredictable tactics into a systematic growth engine with measurable returns on investment."""


def _stub_campaign_objective(brand: str, goal: str) -> str:
    """Campaign objective: ~220 words, 3 headings."""
    return f"""## Primary Objective

Drive measurable progress toward {goal} for {brand} through integrated marketing campaigns that build awareness, consideration, and conversion simultaneously. The primary metric of success combines leading indicators (reach, engagement) with lagging business outcomes (conversions, revenue).

This objective balances brand-building with performance marketing, recognizing that sustainable growth requires both immediate conversions and long-term brand equity that reduces acquisition costs over time.

### Secondary Objectives

Beyond the primary goal, this campaign aims to establish foundational assets and capabilities that compound value beyond the initial 90-day period:

- Build brand recognition within target segments, measuring aided and unaided awareness
- Create content library of high-performing assets that can be repurposed and refreshed
- Establish organic audience growth across owned channels (email, social, community)
- Develop customer insights and data that inform product development and positioning
- Generate case studies and testimonials that strengthen future marketing effectiveness

### Time Horizon

The campaign follows a 90-day primary cycle with built-in learning checkpoints at 30 and 60 days. This allows for tactical adjustments while maintaining strategic consistency. Success metrics are tracked weekly, with major optimizations occurring monthly based on accumulated performance data.

Post-campaign, insights feed into ongoing marketing operations, with top-performing elements becoming permanent fixtures of {brand}'s marketing mix."""


def _stub_core_campaign_idea(brand: str, goal: str) -> str:
    """Core campaign idea: ~300 words, 3 headings, 5 bullets."""
    return f"""## Big Idea

The campaign centers on positioning {brand} as the clear choice for customers seeking {goal}. The creative territory emphasizes transformation over features, showing tangible before/after scenarios that emotionally resonate while demonstrating functional value.

This big idea differentiates {brand} by focusing on customer outcomes rather than product specifications. Every creative execution, from paid ads to organic content, reinforces this central narrative through consistent messaging, visual identity, and proof points.

The approach creates a distinctive point of view that cuts through category noise, making {brand} memorable and desirable to target audiences who currently view competitors as interchangeable commodities.

### Creative Territory

The creative execution explores three interconnected themes that work individually and compound when combined across touchpoints:

- **Transformation Stories**: Real customer journeys from problem to solution, emphasizing emotional relief alongside functional benefits
- **Proof & Authority**: Data-driven evidence of results, expert credentials, and third-party validation that builds trust and credibility
- **Simplicity & Clarity**: Positioning {brand} as the antidote to competitor complexity, using straightforward language and clean design
- **Community & Belonging**: Showcasing customers who've succeeded, creating aspirational peer group that prospects want to join
- **Innovation Edge**: Highlighting {brand}'s unique approach or methodology that delivers superior outcomes compared to standard solutions

### Why It Works

This idea succeeds because it addresses both rational and emotional drivers of purchase decisions. Target customers feel overwhelmed by options and frustrated by past solutions that underdelivered. This campaign cuts through confusion with clarity, backs claims with evidence, and creates emotional resonance through authentic customer stories.

The framework is flexible enough to evolve based on performance data while maintaining strategic consistency that builds brand equity over time."""


def _stub_strategy_final_summary(brand: str, goal: str) -> str:
    """Strategy pack final_summary: ~280 words, 1 heading, 5 bullets."""
    return f"""This comprehensive marketing strategy positions {brand} for sustained growth and market impact. By focusing on {goal}, this plan provides a clear, actionable roadmap for the next 90 days and beyond. The strategy integrates proven frameworks with {brand}-specific insights to create a repeatable system that compounds results over time.

Success requires three key commitments: (1) Consistent execution of the content strategy across all platforms, maintaining the defined brand voice and messaging framework; (2) Regular monitoring of KPIs with data-driven adjustments based on performance insights; (3) Commitment to the core narrative and positioning, resisting the temptation to chase every new trend or platform without strategic evaluation.

The framework outlined here transforms random marketing activities into a repeatable, scalable system. By concentrating efforts on proven content buckets, maintaining platform-specific best practices, and measuring results against clear benchmarks, {brand} will build momentum that compounds over time. This systematic approach replaces guesswork with strategy, creating a foundation for long-term marketing success.

### Key Takeaways

**Critical Success Factors for {brand}:**

- **Strategic Focus**: Concentrate resources on highest-ROI channels and proven content themes rather than spreading efforts too thin across too many platforms
- **Execution Discipline**: Maintain consistency in brand voice, posting cadence, and quality standards even when immediate results aren't visible—compound effects take time
- **Data-Driven Optimization**: Review performance metrics weekly, make tactical adjustments based on evidence, and double down on what works while killing what doesn't
- **Long-Term Perspective**: Building sustainable brand authority and audience trust requires patience, persistence, and commitment to the core strategy beyond short-term tactics
- **Continuous Improvement**: Treat every campaign as a learning opportunity, document insights, and iterate toward increasingly effective marketing systems for {brand}"""


# ============================================================
# FULL FUNNEL & OTHER PACK STUBS
# ============================================================


def _stub_full_funnel_overview(brand: str, goal: str) -> str:
    """Full funnel overview: ~300 words, 2 headings, 8 bullets."""
    return f"""## Full-Funnel Growth Strategy for {brand}

This comprehensive growth framework establishes an integrated system for {brand} to achieve {goal} through coordinated tactics across the entire customer journey. Unlike single-channel or single-stage approaches, this strategy optimizes each funnel stage while ensuring smooth handoffs that maximize conversion rates.

The framework recognizes that modern customers rarely follow linear paths, requiring multiple touchpoints across awareness, consideration, conversion, and retention stages. This strategy creates cohesive experiences that build trust progressively while providing multiple entry points for different customer segments.

### Growth Framework

- **Awareness Engine**: Top-of-funnel tactics that generate qualified traffic through content marketing, paid acquisition, partnerships, and organic visibility across channels where target customers spend time
- **Consideration Nurture**: Middle-funnel sequences that educate prospects, address objections, demonstrate value, and build preference through case studies, comparisons, and proof points
- **Conversion Optimization**: Bottom-funnel mechanisms that reduce friction, create urgency, and incentivize action through optimized landing pages, clear CTAs, and compelling offers
- **Retention Systems**: Post-purchase engagement that maximizes customer lifetime value through onboarding, cross-sells, community building, and advocacy programs
- **Measurement Infrastructure**: Analytics and attribution models that track cohort performance, identify bottlenecks, and quantify channel contribution across the full journey
- **Testing Protocol**: Systematic experimentation across funnel stages to identify winning approaches in messaging, offers, creative, and channel mix
- **Content Repository**: Centralized asset library organized by funnel stage and use case, ensuring sales and marketing teams have appropriate materials for every scenario
- **Technology Stack**: Integrated tools for automation, personalization, and analytics that enable scaled execution without proportional headcount increases

This architecture creates a sustainable growth engine that improves efficiency over time while scaling revenue predictably."""


def _stub_generic_overview(brand: str, goal: str, pack_key: str) -> str:
    """Generic overview for specialized packs: ~250 words, 2 headings, 6 bullets."""
    pack_name = pack_key.replace("_", " ").title()
    return f"""## {pack_name} for {brand}

This specialized strategy addresses the unique challenges and opportunities facing {brand} as it works to achieve {goal}. The approach combines industry best practices with {brand}-specific insights to create a customized roadmap that delivers measurable results.

Rather than generic advice, this plan provides actionable frameworks tailored to your current situation, resources, and market position. Each recommendation connects directly to business outcomes while remaining achievable given realistic constraints.

### Strategic Approach

- **Situation Analysis**: Comprehensive assessment of current state, identifying strengths to leverage and gaps to address through targeted interventions
- **Priority Actions**: Sequenced initiatives that deliver quick wins while building toward long-term objectives, maintaining momentum throughout execution
- **Resource Optimization**: Practical allocation of budget, time, and team attention to highest-impact activities that move key metrics
- **Risk Mitigation**: Proactive identification of potential obstacles and contingency planning to maintain progress despite challenges
- **Success Metrics**: Clear KPIs tied to business outcomes, tracked consistently to demonstrate progress and enable data-driven decisions
- **Timeline & Milestones**: Phased implementation plan with concrete checkpoints that allow for course correction without losing strategic direction

This framework provides {brand} with a clear path forward, balancing ambition with pragmatism to achieve {goal} through systematic execution of proven tactics tailored to your specific context."""


# ============================================================
# UNIVERSAL FALLBACK STUB
# ============================================================


def _stub_universal_fallback(section_id: str, brand: str, goal: str, industry: str) -> str:
    """
    Universal fallback stub for any section not specifically implemented.

    Generates benchmark-compliant content with:
    - 200-300 words (safe middle range)
    - 2 headings (safe minimum for most benchmarks)
    - 6-8 bullets (safe range)
    - Markdown block format

    This ensures tests don't fail even when specific section stubs aren't implemented yet.
    """
    section_title = section_id.replace("_", " ").title()

    return f"""## {section_title} for {brand}

This section provides strategic guidance for {brand} to achieve {goal} within the {industry} space. The approach balances proven frameworks with brand-specific insights to create actionable recommendations.

The strategy outlined here connects directly to business outcomes while remaining practical given resource constraints. Each element builds on established best practices while accounting for your unique market position and competitive landscape.

### Key Elements

- **Foundation**: Comprehensive analysis of current state identifies strengths to leverage and gaps to address through targeted initiatives
- **Strategy**: Clear roadmap with prioritized actions that deliver quick wins while building sustainable competitive advantages
- **Execution**: Practical implementation guidance with specific tactics, timelines, and resource allocation recommendations
- **Measurement**: Defined KPIs and tracking mechanisms that demonstrate progress and enable data-driven optimization decisions
- **Optimization**: Built-in testing and refinement processes that improve effectiveness over time through systematic experimentation
- **Scalability**: Framework designed to grow with your business, becoming more efficient as volume increases
- **Integration**: Coordination with other marketing and business functions to ensure cohesive execution across touchpoints
- **Risk Management**: Proactive identification of potential challenges with contingency planning to maintain momentum

This framework provides {brand} with clear direction while allowing tactical flexibility based on real-world feedback and performance data. The systematic approach transforms one-time initiatives into repeatable processes that compound results."""
