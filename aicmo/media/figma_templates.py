"""
Phase 4.7: Figma Template Engine

Automatically inject generated assets + text into Figma templates.
Supports carousel templates and other layout patterns.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FigmaTemplateConfig:
    """Configuration for a Figma template."""
    
    file_key: str
    """Figma file key identifier"""
    
    page_id: Optional[str] = None
    """Figma page ID (optional, uses first page if not specified)"""
    
    frame_mapping: Dict[str, str] = field(default_factory=dict)
    """Logical slot name → Figma node ID for image placement"""
    
    text_nodes: Dict[str, str] = field(default_factory=dict)
    """Logical text slot name → Figma node ID for text placement"""
    
    name: str = "Untitled Template"
    """Template name for logging/identification"""
    
    description: str = ""
    """Template description"""
    
    template_type: str = "carousel"
    """Template type: carousel, single_image, multi_panel, etc."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional template metadata"""


@dataclass
class CarouselSlide:
    """Single slide in a carousel template."""
    
    slide_id: str
    """Unique slide identifier"""
    
    image_slot: str
    """Slot name for image (maps to frame_mapping)"""
    
    text_slots: List[str] = field(default_factory=list)
    """Slot names for text (maps to text_nodes)"""
    
    order: int = 0
    """Display order (for automatic arrangement)"""


@dataclass
class FigmaTemplateApplication:
    """Result of applying template to assets."""
    
    application_id: str
    """Unique application identifier"""
    
    template_name: str
    """Template that was applied"""
    
    file_key: str
    """Figma file key"""
    
    node_ids: Dict[str, str] = field(default_factory=dict)
    """Applied node IDs for each slot"""
    
    export_url: Optional[str] = None
    """URL to exported/updated Figma file"""
    
    status: str = "applied"
    """Status: applied, exported, failed"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When template was applied"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Application-specific metadata"""


class FigmaTemplateEngine:
    """
    Manages automatic injection of assets and text into Figma templates.
    
    Uses MediaGenerator chain (with Figma provider) to:
    1. Upload/reference generated assets in Figma
    2. Update text nodes with content
    3. Export/sync updated design
    """
    
    def __init__(self, media_engine=None):
        """
        Initialize Figma Template Engine.
        
        Args:
            media_engine: MediaEngine instance for asset loading
        """
        self.media_engine = media_engine
        self.applications: Dict[str, FigmaTemplateApplication] = {}
        self._application_counter = 0
    
    def apply_carousel_template(
        self,
        template: FigmaTemplateConfig,
        assets: Dict[str, Any],
        texts: Dict[str, str],
        export: bool = False,
    ) -> FigmaTemplateApplication:
        """
        Apply carousel template with assets and text.
        
        Steps:
        1. Validate template configuration
        2. Resolve asset references
        3. Prepare text content
        4. Call Figma provider to update nodes
        5. Optionally export updated file
        
        Args:
            template: FigmaTemplateConfig with slots and mappings
            assets: Dict mapping slot names to MediaAsset objects or asset_ids
            texts: Dict mapping text slot names to content strings
            export: Whether to export/sync changes back to Figma
            
        Returns:
            FigmaTemplateApplication with results and node IDs
        """
        try:
            application_id = f"app_{self._application_counter:06d}"
            self._application_counter += 1
            
            logger.info(
                f"Applying carousel template '{template.name}' "
                f"with {len(assets)} assets and {len(texts)} text blocks"
            )
            
            # Validate template
            if not template.file_key:
                logger.error("Template missing file_key")
                return FigmaTemplateApplication(
                    application_id=application_id,
                    template_name=template.name,
                    file_key="",
                    status="failed",
                )
            
            # Resolve assets to node mappings
            node_ids = {}
            for slot_name, asset_ref in assets.items():
                if slot_name not in template.frame_mapping:
                    logger.warning(
                        f"Asset slot '{slot_name}' not in template frame_mapping"
                    )
                    continue
                
                figma_node_id = template.frame_mapping[slot_name]
                node_ids[slot_name] = figma_node_id
                
                logger.debug(
                    f"Mapped asset slot '{slot_name}' to node {figma_node_id}"
                )
            
            # Resolve text slots
            for text_slot, content in texts.items():
                if text_slot not in template.text_nodes:
                    logger.warning(
                        f"Text slot '{text_slot}' not in template text_nodes"
                    )
                    continue
                
                figma_node_id = template.text_nodes[text_slot]
                node_ids[text_slot] = figma_node_id
                
                logger.debug(
                    f"Mapped text slot '{text_slot}' to node {figma_node_id}"
                )
            
            # Create application record
            application = FigmaTemplateApplication(
                application_id=application_id,
                template_name=template.name,
                file_key=template.file_key,
                node_ids=node_ids,
                status="applied",
                metadata={
                    "asset_count": len(assets),
                    "text_count": len(texts),
                    "template_type": template.template_type,
                },
            )
            
            # In real implementation, would call Figma provider here to actually
            # update nodes. For now, we generate stub export URL.
            if export:
                application.export_url = (
                    f"https://figma.com/file/{template.file_key}"
                    f"?node-id={list(node_ids.values())[0] if node_ids else ''}"
                )
                application.status = "exported"
            
            # Store application record
            self.applications[application_id] = application
            
            logger.info(
                f"Successfully applied template, application_id={application_id}"
            )
            
            return application
            
        except Exception as e:
            logger.error(f"Error applying carousel template: {e}", exc_info=True)
            return FigmaTemplateApplication(
                application_id=f"app_error_{self._application_counter:06d}",
                template_name=template.name,
                file_key=template.file_key,
                status="failed",
            )
    
    def apply_single_image_template(
        self,
        template: FigmaTemplateConfig,
        asset: Any,
        metadata: Optional[Dict[str, str]] = None,
        export: bool = False,
    ) -> FigmaTemplateApplication:
        """
        Apply template with single image and metadata.
        
        Args:
            template: FigmaTemplateConfig
            asset: MediaAsset or asset_id
            metadata: Optional metadata dict (title, description, etc.)
            export: Whether to export changes
            
        Returns:
            FigmaTemplateApplication
        """
        # Convert single asset to dict format
        assets_dict = {"main_image": asset}
        texts_dict = metadata or {}
        
        return self.apply_carousel_template(
            template=template,
            assets=assets_dict,
            texts=texts_dict,
            export=export,
        )
    
    def apply_multi_panel_template(
        self,
        template: FigmaTemplateConfig,
        panels: List[Dict[str, Any]],
        export: bool = False,
    ) -> FigmaTemplateApplication:
        """
        Apply template with multiple panels (grid layout).
        
        Args:
            template: FigmaTemplateConfig
            panels: List of dicts with image and text slots
            export: Whether to export changes
            
        Returns:
            FigmaTemplateApplication
        """
        assets_dict = {}
        texts_dict = {}
        
        for i, panel in enumerate(panels):
            if "image" in panel:
                assets_dict[f"panel_{i}_image"] = panel["image"]
            if "title" in panel:
                texts_dict[f"panel_{i}_title"] = panel["title"]
            if "description" in panel:
                texts_dict[f"panel_{i}_description"] = panel["description"]
        
        return self.apply_carousel_template(
            template=template,
            assets=assets_dict,
            texts=texts_dict,
            export=export,
        )
    
    def get_application(self, application_id: str) -> Optional[FigmaTemplateApplication]:
        """Get template application by ID."""
        return self.applications.get(application_id)
    
    def list_applications(self) -> List[FigmaTemplateApplication]:
        """List all template applications."""
        return list(self.applications.values())
    
    def export_application(
        self,
        application_id: str,
        figma_provider=None,
    ) -> Optional[str]:
        """
        Export/sync application to Figma (requires Figma provider).
        
        Args:
            application_id: Application to export
            figma_provider: Figma provider from chain (optional)
            
        Returns:
            Export URL if successful, None otherwise
        """
        app = self.get_application(application_id)
        if not app:
            logger.error(f"Application {application_id} not found")
            return None
        
        try:
            # In real implementation, would use figma_provider to export
            # For now, generate stub URL
            export_url = (
                f"https://figma.com/file/{app.file_key}?v={application_id}"
            )
            
            app.export_url = export_url
            app.status = "exported"
            
            logger.info(f"Exported application {application_id} to Figma")
            return export_url
            
        except Exception as e:
            logger.error(
                f"Error exporting application {application_id}: {e}",
                exc_info=True
            )
            return None
