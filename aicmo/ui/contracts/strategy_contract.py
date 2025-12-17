"""
Strategy Contract: Structured schema for Strategy artifacts.

This contract defines the canonical output format for Strategy generation,
ensuring downstream modules (Creatives, Execution) can reliably consume
strategy decisions.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class ICPSegment:
    """Ideal Customer Profile segment definition"""
    name: str
    who: str  # Role/title
    where: str  # Company/industry
    firmographics: Dict[str, Any] = field(default_factory=dict)  # Size, revenue, location
    demographics: Dict[str, Any] = field(default_factory=dict)  # Age, income, etc.
    psychographics: Dict[str, Any] = field(default_factory=dict)  # Values, pain points
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ICP:
    """Ideal Customer Profile with multiple segments"""
    segments: List[ICPSegment] = field(default_factory=list)
    primary_segment: Optional[str] = None  # Name of primary segment
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "segments": [seg.to_dict() for seg in self.segments],
            "primary_segment": self.primary_segment
        }


@dataclass
class Positioning:
    """Brand positioning statement and differentiation"""
    statement: str  # One-sentence positioning
    differentiators: List[str] = field(default_factory=list)  # Key differences
    competitor_frame: Optional[str] = None  # Who we compete against
    category: Optional[str] = None  # Category we play in
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Messaging:
    """Core messaging framework"""
    core_promise: str  # Primary value proposition
    pain_points: List[str] = field(default_factory=list)  # Problems we solve
    proof_points: List[str] = field(default_factory=list)  # Evidence/credibility
    objections: Dict[str, str] = field(default_factory=dict)  # Objection -> Rebuttal
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContentPillar:
    """Content pillar with angles and examples"""
    name: str
    description: str
    angles: List[str] = field(default_factory=list)
    example_posts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlatformPlan:
    """Platform-specific strategy"""
    platform: str  # LinkedIn, Instagram, etc.
    goals: List[str] = field(default_factory=list)
    content_mix: Dict[str, float] = field(default_factory=dict)  # content_type -> percentage
    cadence: str = ""  # e.g., "3x per week"
    format_priorities: List[str] = field(default_factory=list)  # Carousel, Reel, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CTARules:
    """Call-to-action rules and constraints"""
    allowed_ctas: List[str] = field(default_factory=list)  # Allowed CTA phrases
    primary_offer: str = ""
    funnel_step: str = ""  # Awareness, Consideration, Decision
    forbidden_ctas: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Compliance:
    """Compliance and regulatory constraints"""
    forbidden_claims: List[str] = field(default_factory=list)
    forbidden_topics: List[str] = field(default_factory=list)
    required_disclaimers: List[str] = field(default_factory=list)
    regulatory_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Measurement:
    """KPIs and tracking plan"""
    primary_kpis: List[str] = field(default_factory=list)
    tracking_plan: Dict[str, Any] = field(default_factory=dict)
    reporting_cadence: str = ""
    success_thresholds: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyContract:
    """
    Canonical Strategy Contract schema.
    
    This is the required output format for Strategy artifacts.
    All downstream modules (Creatives, Execution) consume this contract.
    """
    schema_version: int = 1
    
    # Core strategy components (REQUIRED)
    icp: Optional[ICP] = None
    positioning: Optional[Positioning] = None
    messaging: Optional[Messaging] = None
    content_pillars: List[ContentPillar] = field(default_factory=list)
    platform_plan: List[PlatformPlan] = field(default_factory=list)
    cta_rules: Optional[CTARules] = None
    measurement: Optional[Measurement] = None
    
    # Compliance (optional but recommended)
    compliance: Optional[Compliance] = None
    
    # Provenance
    derived_from: Dict[str, Any] = field(default_factory=dict)  # {intake_artifact_id, intake_version}
    
    # Free-form notes (for human-readable context)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        result = {
            "schema_version": self.schema_version,
            "icp": self.icp.to_dict() if self.icp else None,
            "positioning": self.positioning.to_dict() if self.positioning else None,
            "messaging": self.messaging.to_dict() if self.messaging else None,
            "content_pillars": [cp.to_dict() for cp in self.content_pillars],
            "platform_plan": [pp.to_dict() for pp in self.platform_plan],
            "cta_rules": self.cta_rules.to_dict() if self.cta_rules else None,
            "measurement": self.measurement.to_dict() if self.measurement else None,
            "compliance": self.compliance.to_dict() if self.compliance else None,
            "derived_from": self.derived_from,
            "notes": self.notes
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyContract':
        """Create from dict (for deserialization)"""
        # Simple reconstruction - for full validation, use validate_strategy_contract
        return cls(
            schema_version=data.get("schema_version", 1),
            derived_from=data.get("derived_from", {}),
            notes=data.get("notes", "")
        )
    
    def validate(self) -> tuple[bool, List[str], List[str]]:
        """
        Validate this contract.
        
        Returns: (ok: bool, errors: List[str], warnings: List[str])
        """
        errors = []
        warnings = []
        
        if not self.icp or not self.icp.segments:
            errors.append("ICP is required with at least one segment")
        
        if not self.positioning or not self.positioning.statement:
            errors.append("Positioning statement is required")
        
        if not self.messaging or not self.messaging.core_promise:
            errors.append("Core messaging promise is required")
        
        if not self.content_pillars:
            warnings.append("No content pillars defined")
        
        if not self.platform_plan:
            warnings.append("No platform plan defined")
        
        if not self.cta_rules:
            warnings.append("No CTA rules defined")
        
        if not self.measurement:
            warnings.append("No measurement plan defined")
        
        return (len(errors) == 0, errors, warnings)
