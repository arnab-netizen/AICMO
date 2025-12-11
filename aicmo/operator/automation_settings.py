"""
Phase 14 — Automation Settings

Per-brand automation control settings.

Stores and retrieves:
- Automation mode (manual, review_first, full_auto)
- dry_run flag
- Created/updated timestamps

Uses lightweight JSON persistence (can be swapped to SQLite).
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class AutomationSettings:
    """
    Per-brand automation control settings.
    
    Attributes:
        brand_id: Brand UUID
        mode: "manual", "review_first", or "full_auto"
        dry_run: If True, no external APIs called
        created_at: When was this setting created?
        updated_at: When was it last updated?
    """
    
    brand_id: str
    mode: str = "review_first"  # Default: safe mode
    dry_run: bool = True  # Default: safe mode
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "brand_id": self.brand_id,
            "mode": self.mode,
            "dry_run": self.dry_run,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationSettings":
        """Deserialize from dict."""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class AutomationSettingsRepository:
    """
    Repository for automation settings.
    
    Provides CRUD operations with JSON-based persistence.
    Can be swapped to SQLite without changing interface.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize repository.
        
        Args:
            data_dir: Directory for JSON files (default: .aicmo/automation_settings)
        """
        self.data_dir = data_dir or os.path.join(".aicmo", "automation_settings")
        os.makedirs(self.data_dir, exist_ok=True)
        self._index: Dict[str, AutomationSettings] = {}
        self._load_all()
    
    def _get_file_path(self, brand_id: str) -> str:
        """Get file path for a brand."""
        safe_name = brand_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.data_dir, f"{safe_name}.json")
    
    def _load_all(self) -> None:
        """Load all settings from disk."""
        self._index.clear()
        if not os.path.exists(self.data_dir):
            return
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                try:
                    path = os.path.join(self.data_dir, filename)
                    with open(path, "r") as f:
                        data = json.load(f)
                        settings = AutomationSettings.from_dict(data)
                        self._index[settings.brand_id] = settings
                except Exception as e:
                    logger.error(f"Failed to load settings from {filename}: {e}")
    
    def get_settings(self, brand_id: str) -> AutomationSettings:
        """
        Get automation settings for a brand.
        
        Returns default settings (review_first, dry_run=True) if not found.
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            AutomationSettings
        """
        if brand_id in self._index:
            return self._index[brand_id]
        
        # Return safe defaults
        return AutomationSettings(
            brand_id=brand_id,
            mode="review_first",
            dry_run=True,
        )
    
    def save_settings(self, settings: AutomationSettings) -> None:
        """
        Save automation settings for a brand.
        
        Args:
            settings: AutomationSettings to save
        """
        settings.updated_at = datetime.utcnow()
        
        try:
            path = self._get_file_path(settings.brand_id)
            with open(path, "w") as f:
                json.dump(settings.to_dict(), f, indent=2)
            
            self._index[settings.brand_id] = settings
            logger.info(f"Saved automation settings for {settings.brand_id}: {settings.mode}")
        except Exception as e:
            logger.error(f"Failed to save settings for {settings.brand_id}: {e}")
            raise
    
    def list_all(self) -> List[AutomationSettings]:
        """
        List all automation settings.
        
        Returns:
            List of AutomationSettings
        """
        return list(self._index.values())
    
    def delete_settings(self, brand_id: str) -> None:
        """
        Delete automation settings for a brand.
        
        Args:
            brand_id: Brand UUID
        """
        try:
            path = self._get_file_path(brand_id)
            if os.path.exists(path):
                os.remove(path)
            
            if brand_id in self._index:
                del self._index[brand_id]
            
            logger.info(f"Deleted automation settings for {brand_id}")
        except Exception as e:
            logger.error(f"Failed to delete settings for {brand_id}: {e}")
            raise
