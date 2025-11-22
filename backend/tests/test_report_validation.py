"""
Tests for report validation against agency-grade standards.

Tests cover:
1. Canonical briefs (B2C, B2B) producing valid reports
2. Placeholder detection (prohibited phrases, brackets)
3. Required field validation
4. Depth/structure validation
5. Graceful handling of edge cases
"""

import pytest
from datetime import date, timedelta

from aicmo.quality.validators import (
    validate_report,
    has_blocking_issues,
)
from aicmo.io.client_reports import (
    AICMOOutputReport,
    MarketingPlanView,
    StrategyPillar,
    MessagingPyramid,
    CampaignBlueprintView,
    CampaignObjectiveView,
    AudiencePersonaView,
    SocialCalendarView,
    CalendarPostView,
    ActionPlan,
    PersonaCard,
)


@pytest.fixture
def valid_b2c_report():
    """
    Canonical B2C brief producing valid, export-ready report.

    Simulates a typical B2C e-commerce brief (cosmetics, fashion, food).
    """
    today = date.today()
    return AICMOOutputReport(
        marketing_plan=MarketingPlanView(
            executive_summary="Our cosmetics brand targets eco-conscious millennials seeking sustainable beauty alternatives. We will establish thought leadership through educational content, build community through user-generated content campaigns, and drive e-commerce conversion through targeted social commerce strategies.",
            situation_analysis="The sustainable beauty market is growing 12% YoY. Competitors focus on price; our opportunity is premium positioning with environmental impact. Target audience shops on Instagram and TikTok, responds to authenticity and behind-the-scenes content.",
            strategy="Position as the premium, sustainable choice through authentic storytelling. Build community around shared values (environmental impact, ingredient transparency). Drive commerce through influencer partnerships and user-generated content.",
            pillars=[
                StrategyPillar(
                    name="Educational Authority",
                    description="Establish brand as expert in sustainable beauty through in-depth guides, science-backed claims, and educational video series.",
                    kpi_impact="+30% engagement rate on educational content",
                ),
                StrategyPillar(
                    name="Community & Advocacy",
                    description="Build loyal community through user-generated content, exclusive customer spotlights, and sustainability challenges.",
                    kpi_impact="+25% repeat purchase rate",
                ),
                StrategyPillar(
                    name="Social Commerce",
                    description="Drive direct sales through Instagram Shop, TikTok Shop, and shoppable posts with urgency tactics (limited editions, exclusives).",
                    kpi_impact="+40% attributed e-commerce revenue",
                ),
            ],
            messaging_pyramid=MessagingPyramid(
                promise="Beauty that's good for you and the planet",
                key_messages=[
                    "100% natural, cruelty-free ingredients",
                    "Sustainable packaging reduces waste by 60%",
                    "Transparent supply chain from source to shelf",
                ],
                proof_points=[
                    "Certified B Corp status",
                    "3.5M+ community members actively sharing results",
                    "Featured in Vogue, WWD, and TechCrunch",
                ],
                values=["Sustainability", "Transparency", "Authenticity"],
            ),
        ),
        campaign_blueprint=CampaignBlueprintView(
            big_idea="Behind Every Bloom: Our Sustainable Beauty Story",
            objective=CampaignObjectiveView(
                primary="Build brand awareness among eco-conscious beauty shoppers",
                secondary="Drive social commerce conversion through authentic storytelling",
            ),
            audience_persona=AudiencePersonaView(
                name="Eco-Conscious Emma",
                description="28-year-old marketing professional, Instagram/TikTok native, values transparency, willing to pay premium for sustainable products.",
            ),
        ),
        social_calendar=SocialCalendarView(
            start_date=today,
            end_date=today + timedelta(days=30),
            posts=[
                CalendarPostView(
                    date=today,
                    platform="Instagram",
                    theme="Educational",
                    hook="5 ingredients you should NEVER find in skincare",
                    cta="Swipe to learn why these are banned in EU beauty",
                    asset_type="carousel",
                ),
                CalendarPostView(
                    date=today + timedelta(days=1),
                    platform="TikTok",
                    theme="Behind-the-scenes",
                    hook="Watch how we source our rarest botanical extract",
                    cta="Link in bio to see the full supply chain",
                    asset_type="video",
                ),
                CalendarPostView(
                    date=today + timedelta(days=2),
                    platform="Instagram",
                    theme="User-Generated Content",
                    hook="Customer spotlight: Sarah's 30-day skin transformation",
                    cta="Tag us in your before/afters for a feature",
                    asset_type="story",
                ),
                CalendarPostView(
                    date=today + timedelta(days=3),
                    platform="Instagram",
                    theme="Educational",
                    hook="Retinol vs Bakuchiol: which is actually better?",
                    cta="Tap for the science-backed comparison",
                    asset_type="carousel",
                ),
                CalendarPostView(
                    date=today + timedelta(days=4),
                    platform="TikTok",
                    theme="Promotional",
                    hook="LIMITED: Our new rose hip serum is live (only 500 units)",
                    cta="Shop now - link in bio",
                    asset_type="video",
                ),
                CalendarPostView(
                    date=today + timedelta(days=5),
                    platform="LinkedIn",
                    theme="Thought Leadership",
                    hook="The future of sustainable beauty: predictions for 2025",
                    cta="Read our full sustainability report",
                    asset_type="article",
                ),
                CalendarPostView(
                    date=today + timedelta(days=6),
                    platform="Instagram",
                    theme="Community",
                    hook="Join our 30-day sustainability challenge",
                    cta="Tag #SustainableBeautyChallenge to participate",
                    asset_type="carousel",
                ),
            ],
        ),
        action_plan=ActionPlan(
            quick_wins=[
                "Launch educational blog series (3 posts/week for 2 weeks)",
                "Recruit 5 micro-influencers for UGC campaign",
                "Set up Instagram Shop with limited edition product bundle",
            ],
            next_10_days=[
                "Publish first 6 educational blog posts",
                "Receive first UGC submissions from influencer partners",
                "Launch social commerce ad spend ($2k/day budget)",
                "Set up TikTok Shop for direct-to-platform commerce",
            ],
            next_30_days=[
                "Complete 30-day UGC campaign with community spotlights",
                "Launch seasonal limited-edition sustainable packaging variant",
                "Analyze conversion data; optimize top-performing content types",
                "Plan Q1 expansion into YouTube Shorts for education content",
            ],
            risks=[
                "Supply chain delays could impact limited edition launch",
                "TikTok Shop approval may take 5-7 days",
            ],
        ),
        persona_cards=[
            PersonaCard(
                name="Eco-Conscious Emma",
                demographics="28, marketing professional, urban, $75K+ annual income",
                psychographics="Values authenticity, environmental impact, wellness, reads Vogue and Refinery29",
                pain_points=[
                    "Wants sustainable beauty but frustrated by greenwashing",
                    "Concerned about hidden microplastics in mainstream brands",
                    "Limited time to research products; wants curation",
                ],
                triggers=[
                    "Behind-the-scenes content showing transparency",
                    "User testimonials from people like her",
                    "Scientific proof of ingredient safety",
                ],
                objections=[
                    "Premium pricing (product costs 2-3x mainstream)",
                    "Worried about product efficacy vs luxury brands",
                ],
                content_preferences=[
                    "Detailed educational carousels",
                    "Short-form TikTok science explainers",
                    "User-generated transformation content",
                ],
                primary_platforms=["Instagram", "TikTok", "LinkedIn"],
                tone_preference="Authentic, educational, empowering (not preachy)",
            ),
            PersonaCard(
                name="Conscious Mom Maria",
                demographics="42, small business owner, suburban, $120K+ household income",
                psychographics="Prioritizes family health, environmental responsibility, supports women-owned businesses",
                pain_points=[
                    "Wants safe skincare for whole family including kids",
                    "Concerned about long-term chemical exposure",
                    "Wants to support sustainable brands but needs proof",
                ],
                triggers=[
                    "Family-safe certification and ingredient lists",
                    "Stories of women entrepreneurs building sustainable brands",
                    "Long-term health impact research and data",
                ],
                objections=[
                    "Skeptical of sustainability claims; wants third-party verification",
                    "Worried premium products won't work as well",
                ],
                content_preferences=[
                    "In-depth educational articles and guides",
                    "Testimonials from other parents and families",
                    "Certification and transparency documentation",
                ],
                primary_platforms=["Facebook", "Instagram", "Email"],
                tone_preference="Trustworthy, transparent, protective",
            ),
        ],
    )


@pytest.fixture
def valid_b2b_report():
    """
    Canonical B2B brief producing valid, export-ready report.

    Simulates a typical B2B SaaS brief (analytics/marketing tech).
    """
    today = date.today()
    return AICMOOutputReport(
        marketing_plan=MarketingPlanView(
            executive_summary="B2B SaaS analytics platform targeting mid-market CMOs and growth leaders. Strategy focuses on thought leadership in AI-driven marketing intelligence, building credibility through case studies and webinars, and demonstrating ROI through product-led growth and free trial conversion.",
            situation_analysis="The marketing analytics space is crowded with point solutions. Opportunity: integrated platform that combines analytics, AI insights, and predictive modeling. Decision makers research via LinkedIn, industry publications, and peer recommendations. Sales cycle is 60-90 days; buying committees involve CMO, CFO, and IT.",
            strategy="Position as the AI-native analytics platform that enables CMOs to predict campaign ROI before launch. Build credibility through analyst coverage, case studies (1-5M ARR customers), and thought leadership. Drive awareness through LinkedIn, industry events, and peer reviews.",
            pillars=[
                StrategyPillar(
                    name="Thought Leadership & Credibility",
                    description="Establish CEO and product leadership as industry experts through analyst coverage, speaking engagements, webinars, and published research.",
                    kpi_impact="5+ speaking slots at major industry conferences, 10K+ webinar attendees",
                ),
                StrategyPillar(
                    name="Product-Led Growth & Trial Conversion",
                    description="Lower barrier to entry through freemium model and free trial with quick time-to-value. Enable users to see immediate analytics benefits.",
                    kpi_impact="+45% free trial-to-paid conversion rate",
                ),
                StrategyPillar(
                    name="Case Studies & Social Proof",
                    description="Showcase measurable impact with detailed case studies, quantified ROI metrics, and customer testimonials from recognizable brands.",
                    kpi_impact="+60% lead quality, 3-5x deal velocity increase",
                ),
            ],
            messaging_pyramid=MessagingPyramid(
                promise="Know your campaign ROI before you launch",
                key_messages=[
                    "AI-powered predictive analytics for marketing ROI",
                    "Integrates all marketing data in one platform",
                    "Reduce campaign planning time by 40% with AI insights",
                ],
                proof_points=[
                    "Used by 500+ companies in Fortune 1000",
                    "Gartner Magic Quadrant Leader (2024)",
                    "Customers report 3.2x average ROI within 90 days",
                ],
                values=["Predictability", "Integration", "Intelligence"],
            ),
        ),
        campaign_blueprint=CampaignBlueprintView(
            big_idea="Predictive Marketing: The AI Era of Campaign Planning",
            objective=CampaignObjectiveView(
                primary="Build awareness and credibility among CMOs and VP Marketing at 500-5000 employee companies",
                secondary="Generate qualified leads through thought leadership content and product trials",
            ),
            audience_persona=AudiencePersonaView(
                name="Strategic CMO Sarah",
                description="VP/CMO at mid-market (500-5000 employees), reports to CFO/CEO, manages $2-10M budget, owns demand generation and brand. Tech-savvy, reads Forrester/Gartner, active on LinkedIn.",
            ),
        ),
        social_calendar=SocialCalendarView(
            start_date=today,
            end_date=today + timedelta(days=30),
            posts=[
                CalendarPostView(
                    date=today,
                    platform="LinkedIn",
                    theme="Thought Leadership",
                    hook="The average CMO wastes $400K annually on campaigns that miss ROI targets. Here's why.",
                    cta="Comment with your biggest analytics challenge",
                    asset_type="article",
                ),
                CalendarPostView(
                    date=today + timedelta(days=2),
                    platform="LinkedIn",
                    theme="Case Study",
                    hook="How SaaS company XYZ reduced campaign planning time by 40% and increased ROAS by 2.3x",
                    cta="Read the full case study (link in comments)",
                    asset_type="document",
                ),
                CalendarPostView(
                    date=today + timedelta(days=4),
                    platform="LinkedIn",
                    theme="Educational",
                    hook="Predictive analytics 101: 3 metrics every CMO should track before launching campaigns",
                    cta="Save this post for reference",
                    asset_type="carousel",
                ),
                CalendarPostView(
                    date=today + timedelta(days=6),
                    platform="LinkedIn",
                    theme="Webinar Promotion",
                    hook="Upcoming webinar: AI-driven budget allocation in 2025 (with analyst panel)",
                    cta="Register here - 1 seat left",
                    asset_type="event",
                ),
                CalendarPostView(
                    date=today + timedelta(days=8),
                    platform="LinkedIn",
                    theme="Social Proof",
                    hook="Congrats to our newest customers: Nike, Salesforce, and GitLab now using predictive analytics",
                    cta="See all 500+ customers and their results",
                    asset_type="update",
                ),
                CalendarPostView(
                    date=today + timedelta(days=10),
                    platform="LinkedIn",
                    theme="Product Demo",
                    hook="See how our AI identifies your next $500K marketing opportunity (2-min demo)",
                    cta="Watch the demo and start your free trial",
                    asset_type="video",
                ),
                CalendarPostView(
                    date=today + timedelta(days=12),
                    platform="LinkedIn",
                    theme="Industry News",
                    hook="Gartner names us Magic Quadrant Leader. Here's what that means for your marketing team.",
                    cta="Read the analyst report highlights",
                    asset_type="document",
                ),
            ],
        ),
        action_plan=ActionPlan(
            quick_wins=[
                "Reach out to 10 existing customers for case study interviews",
                "Publish CEO thought leadership article on predictive analytics",
                "Finalize webinar speaker lineup (analyst, 2 customers)",
            ],
            next_10_days=[
                "Launch webinar registration campaign (target 1,000 registrations)",
                "Complete 2 detailed case studies with quantified metrics",
                "Submit speaking proposals to 3 major industry conferences",
                "Develop product demo video for LinkedIn",
            ],
            next_30_days=[
                "Host webinar; capture 500+ attendee leads",
                "Publish 4 case studies on website and in sales collateral",
                "Launch LinkedIn thought leadership series (2x weekly posts)",
                "Analyze trial conversion data; optimize onboarding for top ICP segment",
                "Plan Q1 analyst briefing and coverage push",
            ],
            risks=[
                "Getting customer case study participants (incentive required)",
                "Webinar scheduling conflicts with industry events",
            ],
        ),
    )


class TestValidationPassesForCanonicalBriefs:
    """Valid reports from realistic briefs should pass validation."""

    def test_typical_b2c_brief_produces_valid_report(self, valid_b2c_report):
        """B2C cosmetics brief should generate agency-grade report."""
        issues = validate_report(valid_b2c_report)
        assert not has_blocking_issues(
            issues
        ), f"B2C report should pass: {[str(i) for i in issues]}"

    def test_typical_b2b_brief_produces_valid_report(self, valid_b2b_report):
        """B2B SaaS brief should generate agency-grade report."""
        issues = validate_report(valid_b2b_report)
        assert not has_blocking_issues(
            issues
        ), f"B2B report should pass: {[str(i) for i in issues]}"


class TestPlaceholderDetection:
    """Validator should reliably detect placeholder content."""

    def test_hook_idea_placeholder_detected(self, valid_b2c_report):
        """Should detect 'Hook idea for day' placeholder."""
        valid_b2c_report.social_calendar.posts[0].hook = "Hook idea for day 1"
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0, "Should detect hook idea placeholder"
        assert any("hook" in str(e).lower() for e in errors)

    def test_tbd_placeholder_detected(self, valid_b2c_report):
        """Should detect TBD in any field."""
        valid_b2c_report.campaign_blueprint.big_idea = "TBD"
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0, "Should detect TBD placeholder"

    def test_bracketed_placeholder_detected(self, valid_b2c_report):
        """Should detect [BRACKETED] placeholders."""
        valid_b2c_report.marketing_plan.strategy = "Strategy [TO BE DETERMINED]"
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0, "Should detect bracketed placeholder"

    def test_lorem_ipsum_detected(self, valid_b2c_report):
        """Should detect lorem ipsum filler."""
        valid_b2c_report.marketing_plan.executive_summary = "Lorem ipsum dolor sit amet consectetur"
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0, "Should detect lorem ipsum"

    def test_generic_persona_name_detected(self, valid_b2c_report):
        """Should detect generic persona names."""
        if valid_b2c_report.persona_cards:
            valid_b2c_report.persona_cards[0].name = "Generic Persona"
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0, "Should detect generic persona"


class TestRequiredFieldValidation:
    """Validator should enforce presence of required fields."""

    def test_empty_marketing_plan_is_error(self):
        """Marketing plan with missing required fields is an error."""
        report = AICMOOutputReport(
            marketing_plan=MarketingPlanView(
                executive_summary="",
                situation_analysis="",
                strategy="",
            ),
            campaign_blueprint=CampaignBlueprintView(
                big_idea="",
                objective=CampaignObjectiveView(primary=""),
            ),
            social_calendar=SocialCalendarView(
                start_date=date.today(),
                end_date=date.today(),
                posts=[],
            ),
        )
        issues = validate_report(report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0, "Empty report should have errors"

    def test_campaign_blueprint_big_idea_required(self, valid_b2c_report):
        """Campaign blueprint big idea should not be empty."""
        valid_b2c_report.campaign_blueprint.big_idea = ""
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("big idea" in str(e).lower() for e in errors)

    def test_few_social_posts_is_error(self, valid_b2c_report):
        """Social calendar with fewer than 7 posts is an error."""
        valid_b2c_report.social_calendar.posts = []
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("post" in str(e).lower() for e in errors)

    def test_missing_action_plan_is_error(self, valid_b2c_report):
        """Action plan is required."""
        valid_b2c_report.action_plan = None
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("action" in str(e).lower() for e in errors)


class TestStructureValidation:
    """Validator should enforce depth/structure requirements."""

    def test_fewer_than_3_pillars_is_error(self, valid_b2c_report):
        """At least 3 strategic pillars required."""
        valid_b2c_report.marketing_plan.pillars = valid_b2c_report.marketing_plan.pillars[:2]
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("pillar" in str(e).lower() for e in errors)

    def test_generic_pillar_names_are_error(self, valid_b2c_report):
        """Pillar 1, Pillar 2, Pillar 3 are not acceptable."""
        valid_b2c_report.marketing_plan.pillars[0].name = "Pillar 1"
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("pillar" in str(e).lower() and "custom" in str(e).lower() for e in errors)

    def test_generic_campaign_names_are_error(self, valid_b2c_report):
        """Campaign 1, New Campaign are not acceptable."""
        valid_b2c_report.campaign_blueprint.big_idea = "Campaign 1"
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("campaign" in str(e).lower() for e in errors)

    def test_fewer_than_7_calendar_posts_is_error(self, valid_b2c_report):
        """At least 7 posts required in social calendar."""
        valid_b2c_report.social_calendar.posts = valid_b2c_report.social_calendar.posts[:6]
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("post" in str(e).lower() and "7" in str(e) for e in errors)

    def test_fewer_than_5_action_items_is_error(self, valid_b2c_report):
        """At least 5 total action items required."""
        valid_b2c_report.action_plan.quick_wins = []
        valid_b2c_report.action_plan.next_10_days = []
        valid_b2c_report.action_plan.next_30_days = [valid_b2c_report.action_plan.next_30_days[0]]
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert any("action" in str(e).lower() and "5" in str(e) for e in errors)


class TestEdgeCases:
    """Validator should handle edge cases gracefully."""

    def test_empty_optional_sections_allowed(self, valid_b2c_report):
        """Optional sections (performance_review, creatives) can be None."""
        valid_b2c_report.performance_review = None
        valid_b2c_report.creatives = None
        issues = validate_report(valid_b2c_report)
        assert not has_blocking_issues(issues), "Should allow None for optional sections"

    def test_empty_persona_cards_allowed(self, valid_b2c_report):
        """Persona cards are optional."""
        valid_b2c_report.persona_cards = []
        issues = validate_report(valid_b2c_report)
        assert not has_blocking_issues(issues), "Should allow empty persona cards"

    def test_extra_sections_scanned(self, valid_b2c_report):
        """TURBO extra_sections should be scanned for placeholders."""
        valid_b2c_report.extra_sections = {"competitor_analysis": "TBD - to be added later"}
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0, "Should detect TBD in extra sections"


class TestValidationSeverities:
    """Validator should distinguish errors (blocking) from warnings (non-blocking)."""

    def test_placeholder_is_error_not_warning(self, valid_b2c_report):
        """Placeholders should be errors that block export."""
        valid_b2c_report.marketing_plan.strategy += " [TODO: add more]"
        issues = validate_report(valid_b2c_report)
        placeholder_issues = [i for i in issues if "placeholder" in str(i).lower()]
        assert all(i.severity == "error" for i in placeholder_issues)

    def test_brief_summary_is_warning_not_error(self, valid_b2c_report):
        """Too-brief fields are warnings, not errors."""
        valid_b2c_report.marketing_plan.executive_summary = "Short."
        issues = validate_report(valid_b2c_report)
        brief_issues = [i for i in issues if "brief" in str(i).lower()]
        assert all(i.severity == "warning" for i in brief_issues)


class TestReportIssueStructure:
    """ReportIssue dataclass should have expected structure."""

    def test_report_issue_has_required_fields(self, valid_b2c_report):
        """ReportIssue should have section, message, severity."""
        valid_b2c_report.marketing_plan.pillars = []
        issues = validate_report(valid_b2c_report)
        assert len(issues) > 0
        issue = issues[0]
        assert hasattr(issue, "section")
        assert hasattr(issue, "message")
        assert hasattr(issue, "severity")
        assert issue.severity in ("error", "warning")

    def test_report_issue_string_representation(self, valid_b2c_report):
        """ReportIssue should have readable string representation."""
        valid_b2c_report.marketing_plan.pillars = []
        issues = validate_report(valid_b2c_report)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) > 0
        issue_str = str(errors[0])
        assert "[ERROR]" in issue_str
        assert ":" in issue_str


class TestValidationLogging:
    """Validator should log results appropriately."""

    def test_validation_logs_summary(self, valid_b2c_report, caplog):
        """Validator should log issue counts."""
        issues = validate_report(valid_b2c_report)
        # Just verify it completes without error
        assert isinstance(issues, list)
