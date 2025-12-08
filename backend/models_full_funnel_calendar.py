"""
Pydantic models for Full Funnel Growth Suite - 30-Day Content Calendar (Pydantic V2).

Schema-first approach to structured calendar generation with validation
and repair capabilities. Models define the calendar structure before
markdown rendering, enabling deterministic compliance verification.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re


class FullFunnelCalendarItem(BaseModel):
    """
    Single 30-day calendar entry for full_30_day_calendar section.
    """

    day: str = Field(..., description="Day identifier (e.g., 'Day 1', 'Day 15')")
    stage: str = Field(
        ..., description="Funnel stage (Awareness, Consideration, Conversion, Retention, Advocacy)"
    )
    topic: str = Field(
        ..., min_length=10, description="Content topic specific to brand/customer/product/goal"
    )
    format: str = Field(..., description="Content format (Blog, Video, Case Study, etc)")
    channel: str = Field(..., description="Distribution channel (LinkedIn, Twitter, Email, etc)")
    cta: str = Field(
        ..., min_length=3, description="Call-to-action text (e.g., 'Read →', 'Download →')"
    )
    key_points: Optional[List[str]] = Field(
        default_factory=list, description="1-3 key messaging points for markdown bullet generation"
    )

    @field_validator("day")
    @classmethod
    def validate_day_format(cls, v):
        """Ensure day follows 'Day N' or 'Day NN' format."""
        if not re.match(r"^Day \d{1,2}$", v):
            raise ValueError(f"Day must be 'Day N' format, got: {v}")
        return v

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v):
        """Ensure stage is one of the required funnel stages."""
        valid_stages = {"Awareness", "Consideration", "Conversion", "Retention", "Advocacy"}
        if v not in valid_stages:
            raise ValueError(f"Stage must be one of {valid_stages}, got: {v}")
        return v


class FullFunnelCalendar(BaseModel):
    """
    Complete 30-day content calendar for full_funnel_growth_suite.
    """

    items: List[FullFunnelCalendarItem] = Field(
        ..., min_length=30, max_length=30, description="Exactly 30 calendar items, one per day"
    )
    brand: str = Field(..., min_length=2)
    industry: str = Field(..., min_length=3)
    customer: str = Field(..., min_length=5)
    goal: str = Field(..., min_length=5)
    product: str = Field(..., min_length=2)

    @field_validator("items")
    @classmethod
    def validate_unique_days(cls, v):
        """Ensure all days are unique (Day 1 to Day 30)."""
        days = [item.day for item in v]

        # Check for duplicates
        if len(days) != len(set(days)):
            raise ValueError("Days must be unique")

        # Check range is correct
        expected_days = {f"Day {i}" for i in range(1, 31)}
        actual_days = set(days)

        if actual_days != expected_days:
            raise ValueError("Days must be Day 1 through Day 30")

        return v
