from __future__ import annotations

import re
from typing import Any, Dict, Mapping

from backend.agency_report_schema import AgencyReport
from backend.domain_detection import PackDomain
from backend.genericity_scoring import section_quality_score, PLACEHOLDER_PATTERNS
from backend.exceptions import QualityGateFailedError


def plan_agency_report_json(brief: Dict[str, Any], domain: PackDomain) -> Dict[str, Any]:
    """LLM planning step: return compact JSON skeleton for AgencyReport.

    This scaffolding enforces JSON-only outputs in prompts during real use.
    For now, this is a placeholder that callers can replace with an LLM call.
    """
    # Placeholder planning output (keys only, values empty)
    return {
        "brand_name": brief.get("brand_name", ""),
        "industry": brief.get("industry", ""),
        "primary_goal": brief.get("primary_goal", ""),
        "target_audience": brief.get("target_audience", ""),
        "positioning_summary": "",
        "executive_summary": "",
        "situation_analysis": "",
        "key_insights": "",
        "strategy": "",
        "strategic_pillars": [],
        "messaging_pyramid": "",
        "campaign_big_idea": "",
        "campaign_concepts": [],
        "content_calendar_summary": "",
        "content_calendar_table_markdown": "",
        "kpi_framework": "",
        "measurement_plan": "",
        "next_30_days_action_plan": "",
    }


def expand_agency_report_sections(
    plan_json: Dict[str, Any], brief: Dict[str, Any], domain: PackDomain
) -> AgencyReport:
    """Section expansion step: fill each field using focused prompts.

    In this initial scaffolding, we return the AgencyReport constructed from
    the planning JSON. Real implementations should call the LLM per-field,
    apply truncation, and then validate.
    """
    report = AgencyReport.from_dict(plan_json)
    # Deterministic backfill of missing-but-required fields from brief
    report = backfill_agency_report_from_brief(report, brief, domain)
    # Do not validate yet; callers will decide when to enforce gates.
    return report


def assert_agency_grade(report: AgencyReport, domain: PackDomain) -> None:
    reasons: list[str] = []

    key_sections = {
        "executive_summary": report.executive_summary,
        "situation_analysis": report.situation_analysis,
        "strategy": report.strategy,
        "content_calendar_summary": report.content_calendar_summary,
        "kpi_framework": report.kpi_framework,
        "next_30_days_action_plan": report.next_30_days_action_plan,
    }

    for name, text in key_sections.items():
        result = section_quality_score(text, domain)
        if not result.ok:
            reasons.append(f"{name}: " + "; ".join(result.reasons))

    # sanity: brand name appears enough times
    brand_mentions = (report.executive_summary or "").count(report.brand_name or "")
    brand_mentions += (report.strategy or "").count(report.brand_name or "")
    if brand_mentions < 2:
        reasons.append("Brand name not mentioned enough across key sections")

    if reasons:
        raise QualityGateFailedError(reasons)


def backfill_agency_report_from_brief(
    report: AgencyReport,
    brief: Mapping[str, Any],
    domain: PackDomain,
) -> AgencyReport:
    """Deterministically fill any missing-but-required fields from the brief/context.

    This is a last-mile guard: LLM output can still be incomplete, but we should not fail
    validation if the brief already contains enough information to synthesize a minimal
    positioning summary or target audience description.
    """

    def _clean(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _strip_backfill_placeholders(text: str) -> str:
        """Remove any known placeholder tokens from deterministic backfill only.

        We call this only on strings we construct ourselves, not on raw LLM output,
        so it won't mask model quality problems.
        """
        if not text:
            return text
        cleaned = text
        for pattern in PLACEHOLDER_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        # normalize whitespace
        return " ".join(cleaned.split())

    brief_brand = _clean(brief.get("brand_name") or brief.get("brand") or report.brand_name)
    brief_industry = _clean(brief.get("industry") or report.industry)
    brief_goal = _clean(
        brief.get("primary_goal")
        or brief.get("main_goal")
        or brief.get("business_goal")
        or report.primary_goal
    )
    brief_location = _clean(brief.get("city") or brief.get("location") or brief.get("market") or "")
    brief_audience = _clean(
        brief.get("target_audience")
        or brief.get("ideal_customer_profile")
        or brief.get("icp")
        or brief.get("audience")
        or ""
    )

    # 1) positioning_summary
    if not _clean(report.positioning_summary):
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            parts: list[str] = []
            if brief_brand:
                parts.append(f"{brief_brand} is a boutique luxury car dealership")
            elif brief_industry:
                parts.append(f"This brand operates as a specialist in {brief_industry}")

            if brief_location:
                parts.append(f"serving customers in {brief_location}")

            if brief_goal:
                parts.append(f"with a focus on {brief_goal.lower()}")

            summary = ", ".join(parts).rstrip(".")
            if summary:
                report.positioning_summary = summary + "."
        else:
            parts = []
            if brief_brand:
                parts.append(brief_brand)
            if brief_industry:
                parts.append(brief_industry)
            if brief_goal:
                parts.append(brief_goal)
            summary = " – ".join(p for p in parts if p)
            if summary:
                report.positioning_summary = summary

    # 2) target_audience
    if not _clean(report.target_audience):
        if brief_audience:
            report.target_audience = _strip_backfill_placeholders(brief_audience)
        elif domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.target_audience = (
                "Affluent car buyers evaluating luxury and premium vehicles in your city."
            )
        else:
            # Avoid "ideal customer" placeholder pattern
            report.target_audience = "Decision-makers and buyers in your target market."

    # 3) executive_summary
    if not _clean(report.executive_summary):
        # Compose a concise, deterministic summary from brief fields; avoid placeholder phrasing
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            brand = brief_brand or report.brand_name or "Luxotica"
            audience_phrase = brief_audience or "affluent car buyers in the local market"
            location_phrase = f" in {brief_location}" if brief_location else ""
            summary = (
                f"{brand}{location_phrase} delivers a premium, concierge-level buying experience. "
                f"{brand} will increase qualified showroom visits by engaging {audience_phrase} with inventory-led content, "
                f"local SEO, and high-touch follow-up."
            )
            report.executive_summary = _strip_backfill_placeholders(summary)
        else:
            brand = brief_brand or report.brand_name or "Your brand"
            goal_phrase = brief_goal or "growth"
            audience_phrase = brief_audience or "your target market"
            industry_phrase = f" in {brief_industry}" if brief_industry else ""
            summary = (
                f"{brand}{industry_phrase} will execute a focused marketing strategy to achieve {goal_phrase}, "
                f"reaching {audience_phrase}."
            )
            report.executive_summary = _strip_backfill_placeholders(summary)

    # 4) situation_analysis
    if not _clean(report.situation_analysis):
        industry = brief_industry or (
            "automotive" if domain == PackDomain.AUTOMOTIVE_DEALERSHIP else ""
        )
        location_phrase = f" in {brief_location}" if brief_location else ""
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.situation_analysis = (
                f"{brief_brand or 'The dealership'} operates in a competitive luxury car market{location_phrase}. "
                f"Demand is influenced by model availability, financing rates, and seasonal launches. "
                f"Digital channels and local SEO drive showroom traffic; affluent buyers expect concierge-level service."
            )
        else:
            report.situation_analysis = (
                f"The brand competes within the {industry or 'category'} landscape{location_phrase}, with audience needs shaped by "
                f"product differentiation, pricing, and trust. Current marketing relies on owned and paid channels; "
                f"there is opportunity to improve positioning and conversion across the funnel."
            )

    # 5) key_insights
    if not _clean(report.key_insights):
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.key_insights = (
                "Affluent buyers research extensively online before visiting showrooms. "
                "Inventory visibility and transparent pricing increase inquiry rates. "
                "High-touch service and rapid follow-up drive test drives and closes."
            )
        else:
            report.key_insights = (
                "Audience seeks credible, useful content that reduces decision risk. "
                "Clear differentiation and proof points improve conversion. "
                "Consistent nurture increases sales velocity across the funnel."
            )

    # 6) strategy
    if not _clean(report.strategy):
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            brand = brief_brand or report.brand_name or "Luxotica"
            report.strategy = (
                f"{brand} will drive qualified showroom visits through localized SEO, inventory content, and concierge follow-up. "
                "Leverage premium creative highlighting marquee models and ownership benefits; "
                "enable rapid lead routing and high-touch sales workflows to increase test drives and closes."
            )
        else:
            brand = brief_brand or report.brand_name or "Your brand"
            report.strategy = (
                f"Position {brand} with credible, differentiated messaging, execute full-funnel content and campaigns, "
                f"and optimize conversion with clear proof, offers, and nurture. {brand}'s success depends on consistent execution "
                "across all touchpoints."
            )

    # 7) messaging_pyramid
    if not _clean(report.messaging_pyramid):
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.messaging_pyramid = (
                "Promise: Effortless access to luxury vehicles and concierge service.\n"
                "Proof: Certified inventory, transparent pricing, premium ownership benefits.\n"
                "Reasons-to-believe: Expert advisors, rapid test drive scheduling, white-glove delivery."
            )
        else:
            report.messaging_pyramid = (
                "Promise: Clear value and trusted outcomes.\n"
                "Proof: Differentiated product, credible case studies, measurable impact.\n"
                "Reasons-to-believe: Expert team, responsive support, customer success."
            )

    # 8) campaign_big_idea
    if not _clean(report.campaign_big_idea):
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.campaign_big_idea = (
                "Concierge to Keys: a premium, white-glove journey from online research to showroom experience, "
                "highlighting model exclusivity, ownership benefits, and effortless test drive scheduling."
            )
        else:
            report.campaign_big_idea = "Prove the Value: a credible, outcomes-led narrative tying customer needs to differentiated proof and clear CTA."

    # 9) content_calendar_summary and table
    if not _clean(report.content_calendar_summary):
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.content_calendar_summary = (
                "Weekly cadence across SEO blog, inventory spotlights, social showcases, and email nurture. "
                "Align content to model launches and local events; prioritize test drive CTAs and lead capture."
            )
        else:
            report.content_calendar_summary = "Consistent multi-channel publishing across blog, social, email, and ads, aligned to key offers and proof."
    if not _clean(report.content_calendar_table_markdown):
        report.content_calendar_table_markdown = (
            "| Week | Channel | Theme | CTA |\n|---|---|---|---|\n"
            "| 1 | Blog | Positioning article | Learn more |\n"
            "| 1 | Social | Product highlight | Book now |\n"
            "| 1 | Email | Proof + offer | Get offer |"
        )

    # 10) kpi_framework
    if not _clean(report.kpi_framework):
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.kpi_framework = "Leads, test drives, showroom visits, close rate, average order value, and marketing-sourced revenue."
        else:
            report.kpi_framework = (
                "Qualified leads, pipeline, conversion rate, CAC, ROAS, and revenue influenced."
            )

    # 11) measurement_plan
    if not _clean(report.measurement_plan):
        report.measurement_plan = "Implement analytics and CRM attribution; configure campaign UTM, track key events, and produce weekly dashboards."

    # 12) next_30_days_action_plan
    if not _clean(report.next_30_days_action_plan):
        report.next_30_days_action_plan = (
            "Phase 1: finalize messaging and tracking. Phase 2: launch priority content and offers. "
            "Phase 3: optimize lead routing and nurture. Phase 4: review performance and iterate."
        )

    # 13) strategic_pillars
    if not report.strategic_pillars:
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.strategic_pillars = [
                "Premium Experience & Concierge",
                "Inventory Visibility & Local SEO",
                "Lead Routing & Rapid Follow-up",
            ]
        else:
            report.strategic_pillars = [
                "Differentiated Messaging",
                "Full-Funnel Content & Campaigns",
                "Conversion Optimization & Proof",
            ]

    # 14) campaign_concepts
    if not report.campaign_concepts:
        if domain == PackDomain.AUTOMOTIVE_DEALERSHIP:
            report.campaign_concepts = [
                "Model Spotlight Series: weekly premium video + photo sets with test drive CTAs",
                "Owner Benefits Stories: concierge service, maintenance packages, and delivery experience",
                "Local Luxe Events: partnerships and invites with showroom RSVP lead capture",
            ]
        else:
            report.campaign_concepts = [
                "Proof in Action: case-study content with outcomes and clear CTA",
                "Expert Sessions: webinars and live demos to reduce decision risk",
                "Offer-led Sprints: targeted campaigns aligned to buyer pain points",
            ]

    return report
