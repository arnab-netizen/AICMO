"""
Section Prompt Templates for AICMO Report Generation

Defines all available section templates with prompts, names, and output formats.
Each template can be used by the generator to produce a specific section of a report.
"""

from __future__ import annotations

from typing import TypedDict


class SectionTemplate(TypedDict):
    name: str
    prompt: str
    output_format: str  # e.g. "markdown_table", "markdown", "bullets"


SECTION_PROMPT_TEMPLATES: dict[str, SectionTemplate] = {
    # -------------------------------------------------
    # SHARED / CORE SECTIONS
    # -------------------------------------------------
    "overview": {
        "name": "Campaign / Brand Overview",
        "prompt": """
You are a senior marketing strategist.

Write a clear, client-facing overview of the brand and this campaign.

Use the inputs below:
- Brand: {{brand_name}}
- Business type: {{business_type}}
- Location: {{location}}
- Primary product/service: {{primary_offer}}
- Campaign duration: {{campaign_duration}}
- Target audience: {{target_audience}}
- Brand tone: {{brand_tone}}

Output 2–4 concise paragraphs in markdown:
- What the brand does
- Who it serves
- What this campaign/plan is trying to achieve
- Why now (context / timing)
""",
        "output_format": "markdown",
    },
    "campaign_objective": {
        "name": "Campaign Objective",
        "prompt": """
Define 3–5 clear, measurable campaign objectives for {{brand_name}}.

Use SMART style where possible. Consider:
- Business goals (revenue, leads, bookings, footfall, etc.)
- Marketing goals (reach, engagement, CTR, conversion, repeat purchase)
- Timeframe: {{campaign_duration}}
- Budget level: {{budget_level}}

Output as a short introductory paragraph + a markdown bullet list of objectives.
""",
        "output_format": "markdown",
    },
    "core_campaign_idea": {
        "name": "Core Campaign Idea",
        "prompt": """
Develop a big, central campaign idea for {{campaign_name}} for {{brand_name}}.

Requirements:
- 1–2 line campaign theme description
- 3–5 tagline options
- A short explanation of the emotional hook and why it works for {{target_audience}}

Output in markdown with headings:
- Campaign Theme
- Tagline Options
- Rationale
""",
        "output_format": "markdown",
    },
    "messaging_framework": {
        "name": "Messaging Framework",
        "prompt": """
Create a messaging framework for {{brand_name}} for this campaign.

Include:
- Core promise (1–2 lines)
- 3–5 key messages
- Supporting proof points / RTBs
- Tone-of-voice guidelines (3–5 bullets)
- Do / Don't examples (optional but helpful)

Output as markdown with clear subheadings and bullet lists.
""",
        "output_format": "markdown",
    },
    "channel_plan": {
        "name": "Channel Plan",
        "prompt": """
Design a channel plan for this campaign.

Consider channels such as:
- Instagram, Facebook, YouTube, LinkedIn, Twitter/X
- WhatsApp / SMS
- Email
- In-store / offline
- Search / Display / Performance

For each selected channel:
- Role in the funnel (Awareness, Consideration, Conversion, Retention)
- 3–5 tactical actions
- Type of content to focus on
- Success metrics

Output a markdown table with columns:
Channel | Role in Funnel | Key Tactics | Primary KPIs
""",
        "output_format": "markdown_table",
    },
    "audience_segments": {
        "name": "Audience Segments",
        "prompt": """
Define 3–5 key audience segments for {{brand_name}}.

For each segment include:
- Segment name
- Demographics (age, gender, location, income where relevant)
- Psychographics (interests, attitudes, motivations)
- Pain points and needs
- What they value most when choosing {{business_type}}

Output as markdown with one subsection per segment.
""",
        "output_format": "markdown",
    },
    "persona_cards": {
        "name": "Persona Cards",
        "prompt": """
Create 2–4 detailed persona cards based on {{target_audience}} and the audience segments.

Each persona card should include:
- Name (fictional)
- Snapshot (1–2 line summary)
- Demographics
- Goals & motivations
- Pain points and objections
- Preferred channels & content formats
- Buying triggers for this brand/campaign

Output in markdown, with a heading for each persona.
""",
        "output_format": "markdown",
    },
    "creative_direction": {
        "name": "Creative Direction",
        "prompt": """
Define a creative direction for the campaign that matches the brand tone: {{brand_tone}}.

Include:
- Visual style (colors, imagery, composition, mood)
- Typography & layout feel (if relevant)
- Photography / video guidelines
- Do / Don't examples
- Any references to cultural or seasonal context (e.g. festivals, local culture)

Output in markdown with bullet points and short paragraphs.
""",
        "output_format": "markdown",
    },
    "creative_direction_light": {
        "name": "Creative Direction (Light)",
        "prompt": """
Give a lightweight creative direction for social content only.

Focus on:
- Overall look & feel in 5–7 bullets
- Suggested content motifs (what to show in images/videos)
- Simple guidance on colors and mood that match {{brand_tone}}

Keep it short and practical for quick social execution.
""",
        "output_format": "markdown",
    },
    "influencer_strategy": {
        "name": "Influencer Strategy",
        "prompt": """
Design an influencer strategy for {{brand_name}}.

Include:
- Influencer types (nano, micro, macro, local, niche)
- How to select them
- Suggested formats (unboxing, styling, reviews, stories, lives, etc.)
- Collaboration structure (barter, paid, affiliate, event-based)
- Measurement approach (engagement, reach, sales, codes)

Output in markdown with sections and bullet lists.
""",
        "output_format": "markdown",
    },
    "promotions_and_offers": {
        "name": "Promotions & Offers",
        "prompt": """
Propose 3–7 promotional ideas and offers that match {{campaign_objective}} and {{budget_level}}.

For each idea specify:
- Offer name
- Mechanic (e.g. % discount, bundles, loyalty points, limited-time)
- Where it's promoted (channels)
- Intended outcome (e.g. increase AOV, drive first purchase, increase repeat rate)
- Any constraints or notes

Output as a markdown bullet list or table.
""",
        "output_format": "markdown",
    },
    "detailed_30_day_calendar": {
        "name": "Detailed 30-Day Campaign Calendar",
        "prompt": """
Create a detailed 30-day content + campaign calendar for {{primary_channels}}.

Assume one main post per day plus supporting Stories where relevant.

For each day specify:
- Day number (1–30)
- Channel(s)
- Content theme / topic
- Format (Reel, post, story, email, etc.)
- Objective (Awareness, Engagement, Conversion, Retention)
- Notes or CTA

Output as a markdown table:
Day | Channel(s) | Theme / Topic | Format | Objective | Notes
""",
        "output_format": "markdown_table",
    },
    "weekly_social_calendar": {
        "name": "Weekly Social Calendar",
        "prompt": """
Create a simple 7-day social media content calendar for {{primary_channel}}.

For each day:
- Topic / theme
- Format (image, carousel, Reel, Story, etc.)
- Primary CTA

Output a markdown table:
Day | Theme | Format | Primary CTA
""",
        "output_format": "markdown_table",
    },
    "full_30_day_calendar": {
        "name": "Full-Funnel 30-Day Calendar",
        "prompt": """
Design a 30-day full-funnel content calendar across key channels:
{{primary_channels}}.

Balance posts across:
- Awareness
- Consideration
- Conversion
- Retention

For each day include:
- Day
- Funnel stage
- Channel(s)
- Content idea
- Format
- CTA

Output as a markdown table.
""",
        "output_format": "markdown_table",
    },
    "email_and_crm_flows": {
        "name": "Email & CRM Flows",
        "prompt": """
Design email and CRM flows that support this campaign.

Include:
- 1 welcome/onboarding sequence (3–5 emails)
- 1 campaign-specific promo sequence (3–5 emails)
- 1 post-purchase / nurture flow (3–5 emails/messages)

For each flow:
- Flow name
- Objective
- Steps (subject + 1–2 line description)

Output in markdown with nested bullet lists.
""",
        "output_format": "markdown",
    },
    "email_automation_flows": {
        "name": "Email Automation Flows (Retention-Focused)",
        "prompt": """
Create automated email flows with retention in mind.

Include:
- Welcome flow
- Post-purchase flow
- Winback flow
- Browse or cart abandonment (if applicable)

For each:
- Triggers
- Number of emails
- Key message per step
- Main CTA

Output as markdown with clear subheadings.
""",
        "output_format": "markdown",
    },
    "sms_and_whatsapp_flows": {
        "name": "SMS & WhatsApp Flows",
        "prompt": """
Design simple SMS/WhatsApp flows that support retention and CRM.

Include:
- Onboarding message(s)
- Order / booking updates
- Offer notifications
- Re-engagement nudges

Keep copy short and conversational. Output as bullet lists with sample messages.
""",
        "output_format": "markdown",
    },
    "ad_concepts": {
        "name": "Ad Concepts (Single Platform or Mixed)",
        "prompt": """
Create 5–8 ad concepts for {{primary_channels}} for this campaign.

For each concept specify:
- Concept name
- Hook / idea
- Suggested visual
- Copy angle (headline + 1–2 line body)
- Best suited objective (reach, traffic, conversions, etc.)

Output as markdown with one subsection per concept.
""",
        "output_format": "markdown",
    },
    "ad_concepts_multi_platform": {
        "name": "Ad Concepts (Multi-Platform)",
        "prompt": """
Create 5–8 ad concepts, each adapted for at least 2 different platforms
(e.g. Meta, Google, YouTube, LinkedIn depending on context).

For each concept:
- Core idea
- Variant for Platform A
- Variant for Platform B
- Objective
- Notes on targeting if relevant

Output in markdown with clearly labelled subheadings.
""",
        "output_format": "markdown",
    },
    "kpi_and_budget_plan": {
        "name": "KPI & Budget Plan",
        "prompt": """
Create a KPI and budget allocation plan for this campaign.

Assume overall budget level: {{budget_level}}.

Include:
- Main KPIs
- Suggested budget split by channel
- If helpful, split by funnel stage (Awareness, Consideration, Conversion)

Output a markdown table:
Channel / Area | Estimated Budget | Primary KPIs | Notes
""",
        "output_format": "markdown_table",
    },
    "kpi_plan_light": {
        "name": "KPI Plan (Light)",
        "prompt": """
Define a simple KPI plan for the Quick Social Pack.

Include 5–7 key metrics such as:
- Reach
- Impressions
- Engagement rate
- Saves & shares
- Profile visits
- Link clicks
- Follower growth

Output as bullets with 1-line explanation for each.
""",
        "output_format": "markdown",
    },
    "kpi_plan_retention": {
        "name": "Retention KPI Plan",
        "prompt": """
Define 6–10 KPIs focused on retention and CRM.

Consider:
- Repeat purchase rate
- Time between purchases
- Email open/click rates
- Unsubscribe rate
- Loyalty program participation
- Lifetime value

Output as a markdown list with brief explanations.
""",
        "output_format": "markdown",
    },
    "kpi_reset_plan": {
        "name": "KPI Reset Plan (Audit & Revamp)",
        "prompt": """
After auditing current performance, propose a new KPI framework.

Include:
- Which KPIs to stop obsessing over
- Which KPIs to prioritise
- Target ranges or directions (e.g. "increase by 20%+ over 90 days")

Output as bullets grouped under:
- Stop Focusing On
- Start Focusing On
""",
        "output_format": "markdown",
    },
    "execution_roadmap": {
        "name": "Execution Roadmap",
        "prompt": """
Create a practical execution roadmap for {{campaign_duration}}.

Include:
- Phases (Preparation, Launch, Optimization, Wrap-up)
- Key activities per phase
- Who typically owns them (e.g. brand, agency, designer, media buyer)
- Dependencies or prerequisites

Output as a markdown table:
Phase | Timeframe | Key Actions | Owner | Notes
""",
        "output_format": "markdown_table",
    },
    "optimization_opportunities": {
        "name": "Optimization Opportunities",
        "prompt": """
List 8–12 optimization opportunities for this funnel and campaign.

Group them into:
- Quick wins (low effort, high impact)
- Medium-term improvements
- Longer-term strategic changes

Output as markdown bullets under each group.
""",
        "output_format": "markdown",
    },
    "post_campaign_analysis": {
        "name": "Post-Campaign Analysis (Template)",
        "prompt": """
Provide a template-style post-campaign analysis for {{campaign_name}}.

Explain what should be captured after the campaign ends:
- What we planned vs. what happened
- Performance vs. KPIs
- Channel-level insights
- Creative learnings
- Audience learnings
- Recommendations for next campaign

Write as if you are filling in a sample analysis with indicative insights,
not raw numbers, so it looks like a narrative section in a report.
""",
        "output_format": "markdown",
    },
    "final_summary": {
        "name": "Final Summary & Recommendations",
        "prompt": """
Write a concise final summary for the client.

Include:
- What this plan will achieve if executed well
- 3–5 top priorities to focus on first
- Any risks or dependencies to be aware of
- A motivating closing note

Tone: clear, confident, supportive. Output 3–6 short paragraphs.
""",
        "output_format": "markdown",
    },
    # -------------------------------------------------
    # FULL-FUNNEL / MARKET / COMPETITOR
    # -------------------------------------------------
    "market_landscape": {
        "name": "Market Landscape",
        "prompt": """
Describe the market landscape for {{business_type}} in {{location}}.

Include:
- Overall demand context
- Key trends affecting the category
- Channels where competition is active
- Any relevant seasonal or cultural factors

Output 2–4 paragraphs in markdown.
""",
        "output_format": "markdown",
    },
    "competitor_analysis": {
        "name": "Competitor Analysis",
        "prompt": """
Summarise competitor activity for this category.

Assume we have a few typical competitors:
- Local / regional competitors
- 1–2 online-first players (if relevant)
- Any large or national brands in the space

For each type, describe:
- Positioning
- Strengths
- Weaknesses
- What we can do differently

Output as markdown with bullets or mini-sections.
""",
        "output_format": "markdown",
    },
    "funnel_breakdown": {
        "name": "Funnel Breakdown",
        "prompt": """
Break down the current or ideal funnel for {{brand_name}}.

Stages:
- Awareness
- Consideration
- Conversion
- Retention / Loyalty

For each stage:
- What typically happens now
- Key channels
- Friction points
- Opportunities

Output as a markdown table or structured subsections.
""",
        "output_format": "markdown",
    },
    "value_proposition_map": {
        "name": "Value Proposition Map",
        "prompt": """
Define a clear value proposition for {{brand_name}}.

Include:
- Primary value proposition (1–2 sentences)
- 3–6 supporting benefits
- Key differentiators vs typical competitors
- Any proof points (quality, speed, trust, price, service, etc.)

Output as concise markdown with bullets.
""",
        "output_format": "markdown",
    },
    "awareness_strategy": {
        "name": "Awareness Strategy",
        "prompt": """
Craft an awareness strategy for top-of-funnel.

Include:
- Priority channels
- Types of content
- Core messaging angle
- Suggested frequency

Output as markdown bullets and 1–2 short explanatory paragraphs.
""",
        "output_format": "markdown",
    },
    "consideration_strategy": {
        "name": "Consideration Strategy",
        "prompt": """
Describe a consideration-stage strategy.

Focus on:
- How to educate and reassure potential buyers
- Content formats (comparisons, testimonials, demos, etc.)
- Channels and tactics to move users closer to purchase

Output as markdown bullets with a short intro.
""",
        "output_format": "markdown",
    },
    "conversion_strategy": {
        "name": "Conversion Strategy",
        "prompt": """
Define a conversion strategy to turn warm prospects into customers.

Include:
- Tactics for offers, urgency, and social proof
- Landing page / store improvements
- Checkout or booking journey improvements where relevant

Output as markdown with bullets and 1–2 short paragraphs.
""",
        "output_format": "markdown",
    },
    "retention_strategy": {
        "name": "Retention Strategy",
        "prompt": """
Lay out a retention and loyalty strategy.

Include:
- How to get customers to come back
- Role of CRM, loyalty programs, and community
- How often to engage and with what types of content

Output as markdown bullets with short explanations.
""",
        "output_format": "markdown",
    },
    "remarketing_strategy": {
        "name": "Remarketing Strategy",
        "prompt": """
Design a remarketing strategy.

Include:
- Who to remarket to (site visitors, video viewers, engagers, etc.)
- What messages to show at different stages
- Recommended frequency caps
- Any creative notes specific to remarketing

Output as markdown bullets and a short summary.
""",
        "output_format": "markdown",
    },
    # -------------------------------------------------
    # LAUNCH & GTM
    # -------------------------------------------------
    "product_positioning": {
        "name": "Product Positioning",
        "prompt": """
Define the positioning of {{product_name}} in this market.

Include:
- Positioning statement (for X who Y, we are Z that ...)
- 3–5 key benefits
- Why this positioning is credible and differentiated

Output in concise markdown.
""",
        "output_format": "markdown",
    },
    "launch_phases": {
        "name": "Launch Phases",
        "prompt": """
Break the launch into clear phases:

- Pre-launch
- Launch
- Post-launch

For each phase:
- Objectives
- Key activities
- Main channels
- Expected outcomes

Output as a markdown table:
Phase | Objectives | Key Activities | Channels | Outcomes
""",
        "output_format": "markdown_table",
    },
    "launch_campaign_ideas": {
        "name": "Launch Campaign Ideas",
        "prompt": """
Generate 3–5 creative launch campaign ideas.

For each, include:
- Idea name
- Core concept
- Main channels
- Why it fits {{product_name}} and {{target_audience}}

Output as markdown subsections.
""",
        "output_format": "markdown",
    },
    "content_calendar_launch": {
        "name": "Launch Content Calendar",
        "prompt": """
Create a 2–4 week content calendar specifically for launch.

For each day (or at least each key milestone day) specify:
- Day / date label (e.g. Day -7, Day 0, Day +3, etc.)
- Channel
- Content type
- Objective

Output as a markdown table.
""",
        "output_format": "markdown_table",
    },
    "risk_analysis": {
        "name": "Risk Analysis",
        "prompt": """
Identify 5–10 risks that could affect the success of this campaign or launch.

For each:
- Risk description
- Likelihood (Low/Medium/High)
- Impact (Low/Medium/High)
- Mitigation ideas

Output as a markdown table.
""",
        "output_format": "markdown_table",
    },
    # -------------------------------------------------
    # BRAND TURNAROUND
    # -------------------------------------------------
    "brand_audit": {
        "name": "Brand Audit",
        "prompt": """
Summarise a brand audit for {{brand_name}}.

Cover:
- Current perception (based on available context)
- Visual identity state
- Messaging consistency
- Online presence quality
- Strengths and weaknesses

Output in 3–5 short paragraphs with bullet lists.
""",
        "output_format": "markdown",
    },
    "customer_insights": {
        "name": "Customer Insights",
        "prompt": """
List key insights about current or target customers.

Focus on:
- What they're trying to achieve
- What frustrates them about current options
- How they talk about the category
- What would delight them

Output as bullets grouped under 3–5 themes.
""",
        "output_format": "markdown",
    },
    "problem_diagnosis": {
        "name": "Problem Diagnosis",
        "prompt": """
Diagnose why the brand or campaigns are underperforming.

Consider:
- Positioning issues
- Creative/messaging issues
- Channel mix issues
- Funnel and UX issues
- CRM / retention issues

Output as markdown with a short intro + bullet list of key problems.
""",
        "output_format": "markdown",
    },
    "channel_reset_strategy": {
        "name": "Channel Reset Strategy",
        "prompt": """
Propose a channel reset strategy.

Explain:
- Which channels to scale back
- Which channels to invest more in
- Any new channels to test
- How to sequence the changes over 30–90 days

Output as markdown bullets and 1–2 short paragraphs.
""",
        "output_format": "markdown",
    },
    "reputation_recovery_plan": {
        "name": "Reputation Recovery Plan",
        "prompt": """
Design a plan to repair and improve brand reputation.

Include:
- How to monitor sentiment
- How to respond to negative feedback
- Proactive initiatives to rebuild trust
- Timelines and priorities

Output as markdown with clear steps.
""",
        "output_format": "markdown",
    },
    "30_day_recovery_calendar": {
        "name": "30-Day Brand Recovery Calendar",
        "prompt": """
Create a 30-day plan focused on brand recovery.

Each week should have a focus (e.g. listening, fixing basics, proactive storytelling).

For each week:
- Theme
- Key actions
- Channels
- Expected impact

Output as a markdown table:
Week | Theme | Key Actions | Channels | Expected Impact
""",
        "output_format": "markdown_table",
    },
    "turnaround_milestones": {
        "name": "Turnaround Milestones",
        "prompt": """
List 6–10 key milestones for a brand turnaround over 3–6 months.

For each:
- Milestone description
- Target timing
- How to measure success

Output as a markdown bullet list or small table.
""",
        "output_format": "markdown",
    },
    # -------------------------------------------------
    # RETENTION & CRM
    # -------------------------------------------------
    "customer_segments": {
        "name": "Customer Segments (Existing / Past Buyers)",
        "prompt": """
Segment existing customers into 3–6 groups.

Examples:
- New customers
- High-value repeat customers
- Lapsed customers
- Discount seekers
- Loyal advocates

For each segment:
- Description
- Behaviour
- What they need to stay engaged
- Recommended CRM actions

Output as markdown subsections.
""",
        "output_format": "markdown",
    },
    "customer_journey_map": {
        "name": "Customer Journey Map",
        "prompt": """
Outline a customer journey map from first awareness to loyal customer.

Stages:
- Discover
- Consider
- Purchase
- Experience
- Repeat / Advocate

For each stage:
- What the customer is thinking/feeling
- Touchpoints
- Risks / friction
- Opportunities

Output as a markdown table or well-structured bullets.
""",
        "output_format": "markdown",
    },
    "retention_drivers": {
        "name": "Retention Drivers",
        "prompt": """
List 8–12 key drivers of retention for this type of brand.

Examples:
- Product quality
- Reliability
- Personalisation
- Service and support
- Community

Output as markdown bullets with short explanations.
""",
        "output_format": "markdown",
    },
    "loyalty_program_concepts": {
        "name": "Loyalty Program Concepts",
        "prompt": """
Propose 3–5 loyalty or rewards concepts.

For each:
- Concept name
- Mechanic (points, tiers, referrals, perks, etc.)
- Why it fits {{brand_name}} and {{target_audience}}

Output in markdown subsections.
""",
        "output_format": "markdown",
    },
    "winback_sequence": {
        "name": "Winback Sequence",
        "prompt": """
Design a winback flow for lapsed customers.

Include:
- Trigger definition (what 'lapsed' means here)
- 3–5 touchpoints (email/SMS/ads)
- Messaging angle per step
- Offer strategy (if any)

Output as markdown bullet lists.
""",
        "output_format": "markdown",
    },
    "post_purchase_experience": {
        "name": "Post-Purchase Experience",
        "prompt": """
Describe an ideal post-purchase experience that increases satisfaction and repeat purchase.

Include:
- Thank-you and onboarding
- Education and usage tips
- Upsell / cross-sell opportunities
- Review/UGC prompts
- Check-ins

Output as markdown paragraphs with bullets.
""",
        "output_format": "markdown",
    },
    "ugc_and_community_plan": {
        "name": "UGC & Community Plan",
        "prompt": """
Define a plan to encourage user-generated content and community building.

Include:
- Types of UGC to encourage
- Hashtags or campaigns to anchor it
- Incentives (if any)
- How to feature and celebrate customers

Output as markdown bullets and short paragraphs.
""",
        "output_format": "markdown",
    },
    # -------------------------------------------------
    # PERFORMANCE AUDIT & REVAMP
    # -------------------------------------------------
    "account_audit": {
        "name": "Account Audit Summary",
        "prompt": """
Summarise key findings from a performance account audit
(e.g. Meta Ads, Google Ads, etc.).

Include:
- Structure and organisation
- Targeting quality
- Creative rotation and testing
- Tracking/attribution issues
- High-level performance verdict

Output as 3–5 short paragraphs with bullets.
""",
        "output_format": "markdown",
    },
    "campaign_level_findings": {
        "name": "Campaign-Level Findings",
        "prompt": """
Summarise campaign-level findings:

For each main campaign type (prospecting, remarketing, etc.):
- What's working
- What's underperforming
- Possible reasons

Output as markdown with subsections.
""",
        "output_format": "markdown",
    },
    "creative_performance_analysis": {
        "name": "Creative Performance Analysis",
        "prompt": """
Describe how current creatives are performing.

Include:
- Which formats work best
- Which messages or visuals drive better engagement or conversions
- What seems to fatigue quickly

Output as markdown bullets and 1–2 paragraphs of commentary.
""",
        "output_format": "markdown",
    },
    "audience_analysis": {
        "name": "Audience Analysis (Performance)",
        "prompt": """
Analyse audience performance.

Include:
- Which demographic or interest groups appear strongest
- Any obvious mismatches (wasted spend)
- High-level recommendations on audience strategy

Output as markdown bullets and short commentary.
""",
        "output_format": "markdown",
    },
    "competitor_benchmark": {
        "name": "Competitor Benchmark (Performance View)",
        "prompt": """
Provide a simple competitor benchmark from a performance and creative POV.

Include:
- How competitors seem to position themselves
- Types of creatives they use
- What we can learn and adapt (not copy)

Output as markdown bullets.
""",
        "output_format": "markdown",
    },
    "revamp_strategy": {
        "name": "Revamp Strategy",
        "prompt": """
Outline a strategy to revamp the account.

Include:
- Structural changes (campaigns/ad sets/ad groups)
- Creative strategy changes
- Budget allocation shifts
- Testing roadmap

Output as markdown with clear sections.
""",
        "output_format": "markdown",
    },
    # -------------------------------------------------
    # NEW: Missing templates added for Social & Audit packs
    # -------------------------------------------------
    "content_buckets": {
        "name": "Content Buckets & Themes",
        "prompt": """
You are creating CONTENT BUCKETS for a social-first brand.

Based on the brief, brand tone, audience, and category, propose 4–7 clear content buckets.
For each bucket, include:
- Name
- Purpose (why this bucket matters)
- Example post types
- Example angles or hooks

Keep it structured like:

### 1. Bucket Name
- Purpose:
- Example post types:
- Example angles:

Make sure the buckets are distinct from each other and together cover most content needs.
Avoid generic labels like "General" or "Miscellaneous".
""",
        "output_format": "markdown",
    },
    "hashtag_strategy": {
        "name": "Hashtag Strategy",
        "prompt": """
Design a HASHTAG STRATEGY for this brand.

Output in sections:
1) Core Hashtag Principles for the brand
2) Hashtag Pillars:
   - Brand & Campaign
   - Category & Product
   - Audience & Community
   - Location & Event
3) For each pillar, give 8–12 example hashtags:
   - Mix of broad + niche
   - Mix of Hindi/vernacular + English if relevant
4) Platform notes: any differences between Instagram, Facebook, YouTube Shorts, etc.

Format with clear headings and bullet points so it is easy to copy into a client deck.
""",
        "output_format": "markdown",
    },
    "platform_guidelines": {
        "name": "Platform Guidelines",
        "prompt": """
Create PLATFORM GUIDELINES for the key social platforms for this brand.

For each relevant platform (e.g., Instagram, Facebook, YouTube, LinkedIn, WhatsApp):
- Role of the platform in the mix
- Content formats that should be prioritized
- Posting frequency recommendations
- Tone & style notes
- Visual guidelines (high-level)
- Do's and Don'ts

Format:

## Instagram
- Role:
- Priority formats:
- Frequency:
- Tone & style:
- Visual notes:
- Do:
- Don't:

Repeat for each platform that logically fits this brand and audience.
""",
        "output_format": "markdown",
    },
    "new_ad_concepts": {
        "name": "New Ad Concepts",
        "prompt": """
You are designing NEW AD CONCEPTS for a brand whose current performance is weak.

Using the audit insights and revamp strategy:
- Propose 5–8 new ad concepts.
- For each concept include:
  - Concept name
  - Core idea (1–2 lines)
  - Primary objective (awareness, traffic, leads, sales, retention, etc.)
  - Suggested formats (e.g., IG Reel, static, carousel, YT pre-roll, display)
  - Key message / hook lines (2–3 examples)
  - Visual direction (short notes)
  - Target audience / segment

Format clearly with headings per concept:

### Concept 1: Name
- Core idea:
- Objective:
- Formats:
- Key messages:
- Visual direction:
- Target segment:

Make sure concepts are differentiated, practical, and aligned with the brand tone and positioning.
""",
        "output_format": "markdown",
    },
    "new_positioning": {
        "name": "New Positioning",
        "prompt": """
Develop a NEW POSITIONING statement for {{brand_name}} based on the turnaround strategy.

Include:
- Positioning statement (1–2 lines)
- Target audience redefinition
- New value proposition
- Key differentiators vs competitors
- Brand essence / archetype
- Proof points / why believe it

Format:

## New Positioning Statement
> {{positioning}}

## Target Audience Redefinition
{{new_target_audience}}

## Value Proposition
{{new_value_prop}}

## Key Differentiators
- {{diff_1}}
- {{diff_2}}
- {{diff_3}}

## Brand Essence
{{brand_essence}}

## Proof Points
{{proof_points}}
""",
        "output_format": "markdown",
    },
}
