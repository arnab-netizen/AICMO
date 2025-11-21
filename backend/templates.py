"""Text Template Generators (Blank Forms + Blank Reports)."""

from __future__ import annotations

from textwrap import dedent


# =========================
# INPUT – BLANK CLIENT FORM
# =========================


def generate_client_intake_text_template() -> str:
    """Blank, client-facing intake form in clean text/Markdown."""
    return dedent(
        """
        AICMO CLIENT INTAKE FORM
        ========================

        SECTION 1 — BRAND BASICS
        ------------------------
        1. Brand Name:
        2. Website URL:
        3. Social Links (label + URL):
           - 
           - 
        4. Industry / Category:
        5. Location(s):
        6. Type of Business (B2B / B2C / Hybrid):
        7. Brief Description of the Business (1–2 lines):

        SECTION 2 — TARGET AUDIENCE
        ---------------------------
        8. Primary Customer (who buys from you?):
        9. Secondary Customer (optional):
        10. Key Pain Points / Needs (3–5 bullets):
        11. Where do they spend time online?
            (e.g. LinkedIn, Instagram, Facebook, X, YouTube, WhatsApp, Others):

        SECTION 3 — MARKETING GOALS
        ---------------------------
        12. Primary Goal (pick ONE: awareness / leads / sales / app installs / event signups / community growth):
        13. Secondary Goal (optional):
        14. Goal Timeline (1 month / 3 months / 6 months / ongoing):
        15. KPIs that matter most to you (reach / engagement / leads / conversions / ROI / CTR / etc.):

        SECTION 4 — BRAND VOICE & STYLE
        -------------------------------
        16. Tone of Voice (pick 1–2: professional / friendly / bold / emotional / humorous / serious):
        17. Do you have brand guidelines? (Yes / No)
            If yes, please share link:
        18. Preferred colors / visual style:
        19. Competitors you like (links):
        20. Competitors you dislike (links):

        SECTION 5 — PRODUCT / SERVICE DETAILS
        -------------------------------------
        21. Top 3 products/services:
            1.
            2.
            3.
        22. USP of each (why should people choose you?):
        23. Pricing notes (optional):
        24. Current offers / deals:
        25. Proof of value / testimonials (optional):

        SECTION 6 — EXISTING ASSETS & CONSTRAINTS
        -----------------------------------------
        26. Do you already post content? (Yes / No)
            If yes, share links:
        27. Content that worked well:
        28. Content that did not work:
        29. Constraints / limitations (no paid ads, no aggressive tone, etc.):
        30. Platforms you want to focus on:
        31. Platforms you want to avoid:

        SECTION 7 — OPERATIONS
        ----------------------
        32. How often can you approve content? (Daily / Weekly / Monthly / Auto-approve):
        33. Do you need a content calendar? (Yes / No):
        34. Do you need posting & scheduling handled? (Yes / No):
        35. Upcoming events, launches, seasonality or holidays relevant to you:
        36. Monthly budget for promotions (if any): (₹0 / ₹5k–₹20k / ₹20k–₹1L / >₹1L)

        SECTION 8 — STRATEGIC INPUTS
        ----------------------------
        37. 3 adjectives that define your brand:
        38. What does success look like in the next 30 days?
        39. Messages you MUST include:
        40. Messages you MUST avoid:
        41. Tagline (if any):
        42. Anything else we should know?

        Thank you! Please fill this and send it back as:
        - a text/Word/Google Doc, OR
        - a scanned PDF (clearly readable).
        """
    ).strip()


# =========================
# OUTPUT – BLANK REPORTS
# =========================


def generate_blank_marketing_plan_template() -> str:
    return dedent(
        """
        AICMO STRATEGIC MARKETING PLAN
        ==============================

        1. Brand Name:
        2. Timeframe (e.g. Q1 2026):

        EXECUTIVE SUMMARY
        -----------------
        (1–2 paragraphs summarising the overall strategy, goals and expected outcomes.)

        SITUATION ANALYSIS
        ------------------
        Audience Summary:
        Market Context:
        Competitor Snapshot:
        Key Insights:

        STRATEGY
        --------
        Core Message:
        Value Proposition:
        Differentiators:
        Positioning Statement:

        STRATEGIC PILLARS (3–5)
        ------------------------
        Pillar 1 – Name:
        Description:
        KPI Impact:

        Pillar 2 – Name:
        Description:
        KPI Impact:

        (Add more as needed)

        CHANNEL STRATEGY
        ----------------
        For each channel (LinkedIn, Instagram, Facebook, X, Email, Offline):

        Channel:
        Purpose:
        Content Types:
        Frequency:
        KPIs:

        RISKS & MITIGATIONS
        -------------------
        (Key risks and how we will mitigate them.)
        """
    ).strip()


def generate_blank_campaign_blueprint_template() -> str:
    return dedent(
        """
        AICMO CAMPAIGN BLUEPRINT
        ========================

        1. Campaign Name:
        2. Brand Name:

        CAMPAIGN OBJECTIVE
        ------------------
        Primary Objective:
        Secondary Objective (optional):
        KPI Model (what success looks like):

        BIG IDEA
        --------
        (1–2 lines describing the overarching campaign concept.)

        AUDIENCE PERSONA (optional but recommended)
        -------------------------------------------
        Name:
        Demographics:
        Psychographics:
        Pain Points:
        Motivations:

        CREATIVE DIRECTION
        ------------------
        Hooks (headline ideas):
        Messages (key points to communicate):
        Visual Style:
        Emotional Triggers:

        EXECUTION PLAN
        --------------
        Platform-wise Execution Strategy:
        Posting Level / Frequency:
        Content Formats (reels, stories, static, long-form, etc.):

        BUDGET & MEDIA (optional)
        -------------------------
        Notes on budget and paid vs organic split:
        """
    ).strip()


def generate_blank_social_calendar_template() -> str:
    return dedent(
        """
        AICMO SOCIAL CONTENT CALENDAR
        =============================

        Brand Name:
        Period (e.g. March 2026):

        Use the following table as a guide:

        | Date       | Platform | Theme          | Hook                      | CTA             | Asset Type  | Status     | Notes          |
        |------------|----------|----------------|---------------------------|-----------------|------------|-----------|----------------|
        | 2026-03-01 | Instagram| Brand Story    |                           |                 | Reel       | Planned   |                |
        | 2026-03-02 | LinkedIn | Thought Piece  |                           |                 | Text Post  | Planned   |                |
        | ...        | ...      | ...            | ...                       | ...             | ...        | ...       | ...            |

        Status options: planned / draft / approved / published.
        """
    ).strip()


def generate_blank_performance_review_template() -> str:
    return dedent(
        """
        AICMO MONTHLY PERFORMANCE REVIEW
        =================================

        Brand Name:
        Period (e.g. February 2026):

        SUMMARY
        -------
        (Brief summary of the month: key outcomes, context, overall performance.)

        HIGHLIGHTS
        ----------
        Wins:
        Failures:
        Opportunities:

        CHANNEL PERFORMANCE
        -------------------
        For each channel:

        Channel:
        Reach:
        Impressions:
        Engagement:
        Clicks:
        Leads:
        Conversions:
        CTR:
        CPC:
        Notes:

        RECOMMENDATIONS
        ---------------
        Do More Of:
        Do Less Of:
        New Experiments:
        """
    ).strip()
