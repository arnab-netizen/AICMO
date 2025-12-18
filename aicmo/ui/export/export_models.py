"""
Export Models for AICMO Delivery Pack Factory

Defines dataclasses and types for export configuration and results.
"""

from dataclasses import dataclass, field
from typing import Literal, Dict, Any, List, Optional
from datetime import datetime


ExportFormat = Literal["pdf", "pptx", "json", "zip"]


@dataclass
class DeliveryPackConfig:
    """Configuration for generating a delivery package"""
    
    # Context IDs
    engagement_id: str
    client_id: str
    campaign_id: str
    
    # Artifact selection
    include_intake: bool = True
    include_strategy: bool = True
    include_creatives: bool = True
    include_execution: bool = True
    include_monitoring: bool = False
    
    # Export formats
    formats: List[ExportFormat] = field(default_factory=lambda: ["pdf", "json"])
    
    # Branding
    branding: Dict[str, Any] = field(default_factory=lambda: {
        "agency_name": "AICMO",
        "footer_text": "Prepared for {client_name}",
        "logo_path": None,
        "primary_color": "#1E3A8A"
    })
    
    # Optional metadata
    recipients: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "engagement_id": self.engagement_id,
            "client_id": self.client_id,
            "campaign_id": self.campaign_id,
            "include_intake": self.include_intake,
            "include_strategy": self.include_strategy,
            "include_creatives": self.include_creatives,
            "include_execution": self.include_execution,
            "include_monitoring": self.include_monitoring,
            "formats": self.formats,
            "branding": self.branding,
            "recipients": self.recipients,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeliveryPackConfig':
        """Create from dict"""
        return cls(**data)


@dataclass
class DeliveryPackResult:
    """Result from generating a delivery package"""
    
    # Manifest with all metadata
    manifest: Dict[str, Any]
    
    # Generated file paths (format -> filepath)
    files: Dict[str, str]
    
    # Generation timestamp
    generated_at: str
    
    # Output directory
    output_dir: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "manifest": self.manifest,
            "files": self.files,
            "generated_at": self.generated_at,
            "output_dir": self.output_dir
        }
