"""
Full Funnel Calendar Builder - Helper functions for structured calendar generation.

This module provides functions to build FullFunnelCalendar structures from
brief data, then render them to markdown. Separating structure building from
markdown rendering enables validation before rendering.
"""

from backend.models_full_funnel_calendar import FullFunnelCalendarItem, FullFunnelCalendar


def build_full_funnel_calendar(
    brand_name: str,
    industry: str,
    primary_customer: str,
    primary_goal: str,
    product_service: str,
) -> FullFunnelCalendar:
    """
    Build complete 30-day calendar structure from brief context.

    Creates a fully structured FullFunnelCalendar object with all 30 days
    populated with realistic content plans tailored to the brand context.
    """

    # Week 1 (Days 1-7): Awareness/Discovery Phase
    week1_items = [
        FullFunnelCalendarItem(
            day="Day 1",
            stage="Awareness",
            topic=f"Why {primary_customer} choose {product_service} over alternatives",
            format="Blog",
            channel="LinkedIn",
            cta="Read →",
        ),
        FullFunnelCalendarItem(
            day="Day 2",
            stage="Awareness",
            topic=f"{industry} competitive landscape analysis for {primary_goal}",
            format="Infographic",
            channel="Twitter",
            cta="Retweet →",
        ),
        FullFunnelCalendarItem(
            day="Day 3",
            stage="Awareness",
            topic=f"How {brand_name} transforms {primary_customer} workflows",
            format="Case Study",
            channel="Email",
            cta="Download →",
        ),
        FullFunnelCalendarItem(
            day="Day 4",
            stage="Awareness",
            topic=f"{primary_customer} performance metrics with {product_service}",
            format="Data Visualization",
            channel="Instagram",
            cta="Save →",
        ),
        FullFunnelCalendarItem(
            day="Day 5",
            stage="Awareness",
            topic=f"{brand_name}'s methodology for {primary_goal} execution",
            format="Video",
            channel="YouTube",
            cta="Subscribe →",
        ),
        FullFunnelCalendarItem(
            day="Day 6",
            stage="Awareness",
            topic=f"Real {primary_customer} success stories with {product_service}",
            format="Testimonial",
            channel="Facebook",
            cta="Share →",
        ),
        FullFunnelCalendarItem(
            day="Day 7",
            stage="Awareness",
            topic=f"Week 1 recap of {primary_goal} insights for {industry}",
            format="Newsletter",
            channel="Email",
            cta="Read →",
        ),
    ]

    # Week 2 (Days 8-14): Credibility Building
    week2_items = [
        FullFunnelCalendarItem(
            day="Day 8",
            stage="Consideration",
            topic=f"Detailed {primary_customer} migration case study with {product_service}",
            format="Case Study",
            channel="LinkedIn",
            cta="Download →",
        ),
        FullFunnelCalendarItem(
            day="Day 9",
            stage="Consideration",
            topic=f"{industry} specialist webinar on {primary_goal} optimization",
            format="Webinar",
            channel="Email",
            cta="Register →",
        ),
        FullFunnelCalendarItem(
            day="Day 10",
            stage="Consideration",
            topic=f"Feature comparison: {product_service} vs traditional {industry} solutions",
            format="Whitepaper",
            channel="LinkedIn",
            cta="Download →",
        ),
        FullFunnelCalendarItem(
            day="Day 11",
            stage="Consideration",
            topic=f"{primary_customer} video testimonial discussing {primary_goal} ROI",
            format="Video",
            channel="YouTube",
            cta="Watch →",
        ),
        FullFunnelCalendarItem(
            day="Day 12",
            stage="Consideration",
            topic=f"{industry} benchmarking report: {primary_goal} trends and best practices",
            format="Report",
            channel="Email",
            cta="Download →",
        ),
        FullFunnelCalendarItem(
            day="Day 13",
            stage="Consideration",
            topic=f"Roundtable discussion on {primary_goal} strategy in {industry}",
            format="Roundtable",
            channel="LinkedIn",
            cta="Watch →",
        ),
        FullFunnelCalendarItem(
            day="Day 14",
            stage="Consideration",
            topic="Week 2 summary: customer feedback and content performance metrics",
            format="Newsletter",
            channel="Email",
            cta="Read →",
        ),
    ]

    # Week 3 (Days 15-21): Purchase Intent
    week3_items = [
        FullFunnelCalendarItem(
            day="Day 15",
            stage="Conversion",
            topic=f"Live {product_service} demonstration for {primary_customer}",
            format="Live Demo",
            channel="Email",
            cta="Register →",
        ),
        FullFunnelCalendarItem(
            day="Day 16",
            stage="Conversion",
            topic=f"Flash promotion: {primary_goal} solution for {industry} professionals",
            format="Social Post",
            channel="LinkedIn",
            cta="Claim Offer →",
        ),
        FullFunnelCalendarItem(
            day="Day 17",
            stage="Conversion",
            topic=f"Implementation playbook: Getting {primary_customer} started with {product_service}",
            format="Playbook",
            channel="Email",
            cta="Download →",
        ),
        FullFunnelCalendarItem(
            day="Day 18",
            stage="Conversion",
            topic=f"ROI calculator tool for {primary_goal} in {industry}",
            format="Blog",
            channel="Email",
            cta="Calculate Now →",
        ),
        FullFunnelCalendarItem(
            day="Day 19",
            stage="Conversion",
            topic=f"Q&A session: {primary_customer} implementation concerns with {product_service}",
            format="Webinar",
            channel="Email",
            cta="Register →",
        ),
        FullFunnelCalendarItem(
            day="Day 20",
            stage="Conversion",
            topic=f"{primary_customer} early wins achieved with {product_service}",
            format="Case Study",
            channel="LinkedIn",
            cta="Read →",
        ),
        FullFunnelCalendarItem(
            day="Day 21",
            stage="Conversion",
            topic="Week 3 close-out: special offer ending, trial conversions, next steps",
            format="Newsletter",
            channel="Email",
            cta="Act Now →",
        ),
    ]

    # Week 4 (Days 22-30): Adoption & Retention
    week4_items = [
        FullFunnelCalendarItem(
            day="Day 22",
            stage="Retention",
            topic=f"Monthly impact report: {brand_name} growth and {product_service} adoption",
            format="Report",
            channel="Email",
            cta="Read →",
        ),
        FullFunnelCalendarItem(
            day="Day 23",
            stage="Retention",
            topic=f"Final notice: Special offer expires today for {primary_customer}",
            format="Social Post",
            channel="Email",
            cta="Get Access →",
        ),
        FullFunnelCalendarItem(
            day="Day 24",
            stage="Retention",
            topic=f"Onboarding checklist: Getting {primary_customer} to first {primary_goal} win",
            format="Playbook",
            channel="Email",
            cta="Start Here →",
        ),
        FullFunnelCalendarItem(
            day="Day 25",
            stage="Retention",
            topic=f"{brand_name} partnership with {industry} complementary vendor",
            format="Announcement",
            channel="LinkedIn",
            cta="Learn →",
        ),
        FullFunnelCalendarItem(
            day="Day 26",
            stage="Advocacy",
            topic=f"Exclusive early-access preview of upcoming {product_service} feature",
            format="Blog",
            channel="Email",
            cta="Request Access →",
        ),
        FullFunnelCalendarItem(
            day="Day 27",
            stage="Advocacy",
            topic=f"Customer spotlight: {primary_customer} success story with {product_service}",
            format="Case Study",
            channel="LinkedIn",
            cta="Read →",
        ),
        FullFunnelCalendarItem(
            day="Day 28",
            stage="Retention",
            topic=f"Advanced {product_service} techniques for {primary_goal} maximization",
            format="Ebook",
            channel="Email",
            cta="Download →",
        ),
        FullFunnelCalendarItem(
            day="Day 29",
            stage="Retention",
            topic=f"Success dashboard walkthrough: Tracking {primary_goal} progress",
            format="Video",
            channel="YouTube",
            cta="Watch →",
        ),
        FullFunnelCalendarItem(
            day="Day 30",
            stage="Advocacy",
            topic=f"{brand_name} roadmap preview: next month's {product_service} updates",
            format="Blog",
            channel="Email",
            cta="Subscribe →",
        ),
    ]

    all_items = week1_items + week2_items + week3_items + week4_items

    calendar = FullFunnelCalendar(
        items=all_items,
        brand=brand_name,
        industry=industry,
        customer=primary_customer,
        goal=primary_goal,
        product=product_service,
    )

    return calendar


def render_calendar_to_markdown(calendar: FullFunnelCalendar) -> str:
    """
    Render FullFunnelCalendar structured data to markdown string.

    Produces deterministic markdown output that meets all benchmark constraints.
    """

    b = calendar.brand
    cust = calendar.customer
    goal = calendar.goal
    prod = calendar.product

    intro = f"""## Full 30-Day Content Calendar for {b}

{b} launches this 30-day calendar to guide {cust} toward {goal}. Content moves prospects from discovery through purchase decision and month-one success with {prod}.
"""

    # Week 1
    w1_items = [item for item in calendar.items if 1 <= int(item.day.split()[1]) <= 7]
    w1_markdown = f"""### Week 1 – Discovery Phase (Days 1-7)

{b} introduces itself to {cust}. Early-week content establishes credibility. Mid-week pieces highlight competitive advantages.

| Day | Stage | Topic | Format | Channel | CTA |
|-----|-------|-------|--------|---------|-----|
"""
    for item in w1_items:
        w1_markdown += f"| {item.day} | {item.stage} | {item.topic} | {item.format} | {item.channel} | {item.cta} |\n"

    # Week 2
    w2_items = [item for item in calendar.items if 8 <= int(item.day.split()[1]) <= 14]
    w2_markdown = f"""
### Week 2 – Credibility Building (Days 8-14)

Week 2 establishes proof through case studies and expert commentary. {b} demonstrates specific {prod} capabilities that drive {goal}.

"""
    for item in w2_items:
        w2_markdown += f"- **{item.day}**: {item.topic}. Distributed via {item.channel}.\n"

    # Week 3
    w3_items = [item for item in calendar.items if 15 <= int(item.day.split()[1]) <= 21]
    w3_markdown = f"""
### Week 3 – Purchase Intent (Days 15-21)

Week 3 moves {cust} toward purchasing {prod}. Interactive demos showcase functionality. Limited offers create urgency.

"""
    for item in w3_items:
        w3_markdown += f"- **{item.day}**: {item.topic}. Distributed via {item.channel}.\n"

    # Week 4
    w4_items = [item for item in calendar.items if 22 <= int(item.day.split()[1]) <= 30]
    w4_markdown = f"""
### Week 4 – Adoption & Retention (Days 22-30)

Week 4 closes deals and ensures new {cust} success. Onboarding content helps {prod} users achieve {goal} in first 30 days.

"""
    for item in w4_items:
        w4_markdown += f"- **{item.day}**: {item.topic}. Distributed via {item.channel}.\n"

    # Campaign framework
    framework = f"""
## Campaign Framework

**Timing**: {b} distributes email mornings (8am). Social posts follow by 10am. Video publishes afternoons (2pm). Evening newsletter recaps.

**Channels**: Email, LinkedIn, Twitter, Instagram, Facebook, YouTube receive tailored versions. Platform-specific formatting optimizes engagement.

**Progression**: Week 1 establishes awareness and {b} credibility. Week 2 proves {prod} success with evidence. Week 3 converts {cust}. Week 4 ensures {prod} adoption and {goal} achievement.
"""

    return intro + w1_markdown + w2_markdown + w3_markdown + w4_markdown + framework
