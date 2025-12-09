"""Learning and Kaizen domain models.

Domain models for the learning/Kaizen system that aggregates insights
from historical events to influence future decisions.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class KaizenContext(BaseModel):
    """
    Aggregated learning context for a project or client.
    
    Built from historical learning events, this context summarizes
    patterns and insights that should influence future decisions:
    - Which channels perform best/worst
    - Which creative patterns work/fail
    - What causes project delays
    - What wins pitches
    
    Used by service layers to make Kaizen-informed decisions.
    """
    
    project_id: Optional[Union[int, str]] = None
    client_id: Optional[Union[int, str]] = None
    brand_name: Optional[str] = None
    
    # Media & Analytics insights
    best_channels: List[str] = Field(default_factory=list)
    weak_channels: List[str] = Field(default_factory=list)
    channel_performance: Dict[str, float] = Field(default_factory=dict)
    
    # Creative insights
    high_performing_creatives: List[Dict[str, Any]] = Field(default_factory=list)
    rejected_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    successful_hooks: List[str] = Field(default_factory=list)
    failed_hooks: List[str] = Field(default_factory=list)
    
    # Pitch & Brand insights
    pitch_win_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    successful_positioning: List[str] = Field(default_factory=list)
    effective_tones: List[str] = Field(default_factory=list)
    
    # Project Management insights
    delay_risks: List[Dict[str, Any]] = Field(default_factory=list)
    capacity_issues: List[str] = Field(default_factory=list)
    common_blockers: List[str] = Field(default_factory=list)
    
    # Client Portal insights
    approval_patterns: Dict[str, Any] = Field(default_factory=dict)
    frequent_feedback_themes: List[str] = Field(default_factory=list)
    
    # Metadata
    total_events_analyzed: int = 0
    context_built_at: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": 123,
                "brand_name": "TechCorp",
                "best_channels": ["meta", "google"],
                "weak_channels": ["twitter"],
                "pitch_win_patterns": [{"industry": "tech", "size": "startup", "success_rate": 0.8}],
                "rejected_patterns": [{"hook": "generic startup story", "rejection_count": 3}],
                "total_events_analyzed": 42
            }
        }
    }


class KaizenInsight(BaseModel):
    """
    A single actionable insight derived from learning events.
    
    Used to represent specific recommendations or observations
    that can be acted upon.
    """
    
    category: str  # pitch, brand, media, creative, pm, portal
    insight_type: str  # recommendation, warning, pattern, trend
    description: str
    confidence: float = 0.5  # 0.0 to 1.0
    supporting_events: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
