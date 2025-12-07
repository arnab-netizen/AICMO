from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


MAX_FIELD_LENGTH = 3000
MAX_LIST_ITEMS = 50
MAX_LIST_ITEM_LENGTH = 600


def _trim_text(value: str, max_len: int = MAX_FIELD_LENGTH) -> str:
    # Normalize and hard-trim overly long fields
    v = (value or "").strip()
    if len(v) > max_len:
        v = v[:max_len]
    return v


def _trim_list(items: List[str]) -> List[str]:
    if not items:
        return []
    trimmed: List[str] = []
    for item in items[:MAX_LIST_ITEMS]:
        i = _trim_text(item, MAX_LIST_ITEM_LENGTH)
        if i:
            trimmed.append(i)
    return trimmed


@dataclass
class AgencyReport:
    # Core identity and positioning
    brand_name: str
    industry: str
    primary_goal: str
    target_audience: str
    positioning_summary: str

    # Executive-level narrative
    executive_summary: str
    situation_analysis: str
    key_insights: str

    # Strategy and frameworks
    strategy: str
    strategic_pillars: List[str]
    messaging_pyramid: str

    # Campaign concepting
    campaign_big_idea: str
    campaign_concepts: List[str]

    # Calendar and execution
    content_calendar_summary: str
    content_calendar_table_markdown: str

    # Measurement and next steps
    kpi_framework: str
    measurement_plan: str
    next_30_days_action_plan: str

    def validate(self) -> None:
        """Validate required fields and normalize content lengths.

        - Ensures required string fields are non-empty after trimming.
        - Trims each string to MAX_FIELD_LENGTH.
        - Trims list items and caps list sizes.
        """

        # Normalize strings
        for field_name, value in self._iter_string_fields().items():
            trimmed = _trim_text(value)
            if not trimmed:
                raise ValueError(f"Missing or empty required field: {field_name}")
            setattr(self, field_name, trimmed)

        # Normalize lists
        self.strategic_pillars = _trim_list(self.strategic_pillars)
        self.campaign_concepts = _trim_list(self.campaign_concepts)

        # Lists should not be empty for sections that expect multiple items
        if not self.strategic_pillars:
            raise ValueError(
                "Missing required content: strategic_pillars must contain at least one item"
            )
        if not self.campaign_concepts:
            raise ValueError(
                "Missing required content: campaign_concepts must contain at least one item"
            )

    def _iter_string_fields(self) -> Dict[str, str]:
        # Return a mapping of all string fields for normalization/validation
        return {
            "brand_name": self.brand_name,
            "industry": self.industry,
            "primary_goal": self.primary_goal,
            "target_audience": self.target_audience,
            "positioning_summary": self.positioning_summary,
            "executive_summary": self.executive_summary,
            "situation_analysis": self.situation_analysis,
            "key_insights": self.key_insights,
            "strategy": self.strategy,
            "messaging_pyramid": self.messaging_pyramid,
            "campaign_big_idea": self.campaign_big_idea,
            "content_calendar_summary": self.content_calendar_summary,
            "content_calendar_table_markdown": self.content_calendar_table_markdown,
            "kpi_framework": self.kpi_framework,
            "measurement_plan": self.measurement_plan,
            "next_30_days_action_plan": self.next_30_days_action_plan,
        }

    def to_pdf_context(self) -> Dict[str, Any]:
        """Flatten into a dict suitable for Jinja/HTML templates."""
        ctx: Dict[str, Any] = asdict(self)
        return ctx

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgencyReport":
        """Construct an AgencyReport from a dict; callers should run validate()."""
        return cls(
            brand_name=data.get("brand_name", ""),
            industry=data.get("industry", ""),
            primary_goal=data.get("primary_goal", ""),
            target_audience=data.get("target_audience", ""),
            positioning_summary=data.get("positioning_summary", ""),
            executive_summary=data.get("executive_summary", ""),
            situation_analysis=data.get("situation_analysis", ""),
            key_insights=data.get("key_insights", ""),
            strategy=data.get("strategy", ""),
            strategic_pillars=list(data.get("strategic_pillars", []) or []),
            messaging_pyramid=data.get("messaging_pyramid", ""),
            campaign_big_idea=data.get("campaign_big_idea", ""),
            campaign_concepts=list(data.get("campaign_concepts", []) or []),
            content_calendar_summary=data.get("content_calendar_summary", ""),
            content_calendar_table_markdown=data.get("content_calendar_table_markdown", ""),
            kpi_framework=data.get("kpi_framework", ""),
            measurement_plan=data.get("measurement_plan", ""),
            next_30_days_action_plan=data.get("next_30_days_action_plan", ""),
        )


def agency_report_to_pdf_context(report: AgencyReport) -> Dict[str, Any]:
    """Helper for callers that prefer a standalone function."""
    return report.to_pdf_context()
