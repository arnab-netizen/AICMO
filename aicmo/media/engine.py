"""
Phase 4: Media Management Engine

Manages media asset lifecycle, reuse, performance tracking, and optimization.
Integrates with Phase 2 publishing and Phase 3 analytics.

Phase 4.5: Media Generation and Figma Export
- generate_asset_from_prompt(): Create assets from text descriptions
- export_asset_to_figma(): Export assets to Figma designs
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from .models import (
    MediaAsset,
    MediaLibrary,
    MediaPerformance,
    MediaOptimizationSuggestion,
    MediaType,
    MediaStatus,
)

logger = logging.getLogger(__name__)

# Module-level singleton for testing
_media_engine: Optional["MediaEngine"] = None


class MediaEngine:
    """Main engine for managing media assets and performance."""
    
    def __init__(self):
        """Initialize media engine."""
        self.libraries: Dict[str, MediaLibrary] = {}
        self.assets: Dict[str, MediaAsset] = {}
        self.performance_data: Dict[str, MediaPerformance] = {}
        self.suggestions: Dict[str, MediaOptimizationSuggestion] = {}
    
    def create_library(
        self,
        name: str,
        description: str = "",
        owner: str = "",
    ) -> MediaLibrary:
        """
        Create a new media library.
        
        Args:
            name: Library name
            description: Library description
            owner: Owner/creator
            
        Returns:
            New MediaLibrary
        """
        library = MediaLibrary(
            name=name,
            description=description,
            owner=owner,
        )
        self.libraries[library.library_id] = library
        return library
    
    def add_asset_to_library(
        self,
        library_id: str,
        asset: MediaAsset,
    ) -> Optional[MediaAsset]:
        """
        Add asset to library.
        
        Args:
            library_id: Target library ID
            asset: Asset to add
            
        Returns:
            Asset if added, None if library not found
        """
        if library_id not in self.libraries:
            return None
        
        library = self.libraries[library_id]
        library.add_asset(asset)
        self.assets[asset.asset_id] = asset
        return asset
    
    def find_duplicate_assets(
        self,
        file_hash: str,
    ) -> List[MediaAsset]:
        """
        Find existing assets with same file hash.
        
        Args:
            file_hash: SHA256 hash of file
            
        Returns:
            List of matching assets
        """
        return [
            asset for asset in self.assets.values()
            if asset.content_hash == file_hash
        ]
    
    def get_asset_variants(
        self,
        asset_id: str,
    ) -> List[Tuple[str, str]]:
        """
        Get variants of an asset (different sizes, formats).
        
        Args:
            asset_id: Parent asset ID
            
        Returns:
            List of (variant_id, variant_name) tuples
        """
        # TODO: Track variants separately
        # For now, return empty list
        return []
    
    def track_asset_performance(
        self,
        asset_id: str,
        campaign_id: str,
        channel: str,
        impressions: int = 0,
        clicks: int = 0,
        engagements: int = 0,
        conversions: int = 0,
        shares: int = 0,
        comments: int = 0,
    ) -> MediaPerformance:
        """
        Track asset performance in a campaign.
        
        Args:
            asset_id: Asset ID
            campaign_id: Campaign ID
            channel: Publishing channel
            impressions: Number of impressions
            clicks: Number of clicks
            engagements: Number of engagements
            conversions: Number of conversions
            shares: Number of shares
            comments: Number of comments
            
        Returns:
            MediaPerformance tracking object
        """
        performance = MediaPerformance(
            asset_id=asset_id,
            campaign_id=campaign_id,
            channel=channel,
            impressions=impressions,
            clicks=clicks,
            engagements=engagements,
            conversions=conversions,
            shares=shares,
            comments=comments,
        )
        performance.calculate_rates()
        
        self.performance_data[performance.performance_id] = performance
        
        # Update asset usage
        if asset_id in self.assets:
            self.assets[asset_id].mark_used(campaign_id)
        
        return performance
    
    def get_asset_performance(
        self,
        asset_id: str,
    ) -> List[MediaPerformance]:
        """
        Get all performance records for an asset.
        
        Args:
            asset_id: Asset ID
            
        Returns:
            List of performance records
        """
        return [
            perf for perf in self.performance_data.values()
            if perf.asset_id == asset_id
        ]
    
    def get_best_performing_assets(
        self,
        campaign_id: str,
        limit: int = 5,
    ) -> List[Tuple[str, float]]:
        """
        Get best-performing assets in a campaign.
        
        Args:
            campaign_id: Campaign ID
            limit: Max results
            
        Returns:
            List of (asset_id, ctr) tuples
        """
        campaign_perf = [
            perf for perf in self.performance_data.values()
            if perf.campaign_id == campaign_id
        ]
        
        sorted_perf = sorted(
            campaign_perf,
            key=lambda p: p.ctr,
            reverse=True
        )
        
        return [
            (perf.asset_id, perf.ctr)
            for perf in sorted_perf[:limit]
        ]
    
    def suggest_optimization(
        self,
        asset_id: str,
        optimization_type: str,
        description: str,
        estimated_improvement: float = 0.0,
        priority: str = "medium",
    ) -> MediaOptimizationSuggestion:
        """
        Create optimization suggestion for asset.
        
        Args:
            asset_id: Asset to optimize
            optimization_type: Type of optimization
            description: Description of suggestion
            estimated_improvement: Expected CTR improvement (percentage)
            priority: low, medium, high
            
        Returns:
            MediaOptimizationSuggestion
        """
        suggestion = MediaOptimizationSuggestion(
            asset_id=asset_id,
            type=optimization_type,
            description=description,
            estimated_improvement=estimated_improvement,
            priority=priority,
        )
        self.suggestions[suggestion.suggestion_id] = suggestion
        return suggestion
    
    def auto_suggest_optimizations(
        self,
        asset_id: str,
        ctr_threshold: float = 0.05,
    ) -> List[MediaOptimizationSuggestion]:
        """
        Auto-generate optimization suggestions based on performance.
        
        Args:
            asset_id: Asset to analyze
            ctr_threshold: CTR below this triggers suggestions
            
        Returns:
            List of suggestions
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return []
        
        perf_records = self.get_asset_performance(asset_id)
        if not perf_records:
            return []
        
        avg_ctr = sum(p.ctr for p in perf_records) / len(perf_records)
        suggestions = []
        
        # Low CTR suggestion
        if avg_ctr < ctr_threshold:
            sugg = self.suggest_optimization(
                asset_id=asset_id,
                optimization_type="refresh_design",
                description="Asset CTR below threshold. Consider refreshing design.",
                estimated_improvement=15.0,
                priority="high",
            )
            suggestions.append(sugg)
        
        # File size optimization
        if asset.metadata and asset.metadata.file_size_mb() > 5:
            sugg = self.suggest_optimization(
                asset_id=asset_id,
                optimization_type="compress",
                description="Large file size. Consider compression.",
                estimated_improvement=5.0,
                priority="medium",
            )
            suggestions.append(sugg)
        
        # Format optimization
        if asset.media_type == MediaType.IMAGE:
            sugg = self.suggest_optimization(
                asset_id=asset_id,
                optimization_type="convert_to_webp",
                description="Convert to WebP format for better compression.",
                estimated_improvement=3.0,
                priority="low",
            )
            suggestions.append(sugg)
        
        return suggestions
    
    def get_library_statistics(
        self,
        library_id: str,
    ) -> Dict[str, any]:
        """
        Get statistics for a library.
        
        Args:
            library_id: Library ID
            
        Returns:
            Statistics dictionary
        """
        if library_id not in self.libraries:
            return {}
        
        library = self.libraries[library_id]
        
        # Calculate usage stats
        total_usage = sum(a.usage_count for a in library.assets.values())
        avg_usage = total_usage / len(library.assets) if library.assets else 0
        
        # Calculate performance stats
        lib_assets = set(library.assets.keys())
        lib_perf = [
            p for p in self.performance_data.values()
            if p.asset_id in lib_assets
        ]
        
        avg_ctr = sum(p.ctr for p in lib_perf) / len(lib_perf) if lib_perf else 0
        
        return {
            "asset_count": library.asset_count(),
            "total_size_mb": library.total_size_mb(),
            "total_usage": total_usage,
            "average_usage_per_asset": avg_usage,
            "total_campaigns": len({
                campaign
                for a in library.assets.values()
                for campaign in a.campaigns_used_in
            }),
            "average_ctr": avg_ctr,
            "tags": len(library.tags),
            "categories": len(library.categories),
        }
    
    def compare_media_formats(
        self,
        asset_id: str,
    ) -> Dict[str, float]:
        """
        Compare performance across variants/formats.
        
        Args:
            asset_id: Parent asset ID
            
        Returns:
            Format → CTR mapping
        """
        perf_records = self.get_asset_performance(asset_id)
        
        format_performance = {}
        for perf in perf_records:
            key = f"{perf.channel}"
            if key not in format_performance:
                format_performance[key] = perf.ctr
            else:
                # Average multiple performances
                format_performance[key] = (
                    format_performance[key] + perf.ctr
                ) / 2
        
        return format_performance
    
    # Phase 4.5: Media generation and Figma export
    
    async def generate_asset_from_prompt(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        library_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[MediaAsset]:
        """
        Generate image asset from text prompt using multi-provider chain.
        
        Steps:
        1. Get MediaGeneratorChain from factory
        2. Call chain.execute_generate_image() with fallback
        3. Convert generation result into MediaAsset
        4. Add asset to library (default or specified)
        5. Return new asset
        
        Args:
            prompt: Text description of image to generate
            width: Image width (default 1024)
            height: Image height (default 1024)
            library_id: Library to add to (optional, uses default)
            **kwargs: Provider-specific options
            
        Returns:
            Generated MediaAsset with proper library integration, or None on failure
        """
        try:
            from ..gateways.factory import get_media_generator_chain
            from .models import MediaDimensions, MediaMetadata
            
            # Get the provider chain
            chain = get_media_generator_chain()
            if not chain:
                logger.error("Failed to get media generator chain")
                return None
            
            # Generate image with provider fallback
            generated_image = await chain.execute_generate_image(
                prompt=prompt,
                width=width,
                height=height,
                **kwargs,
            )
            
            if not generated_image:
                logger.error("All media generation providers failed")
                return None
            
            # Create MediaAsset from generated image
            asset = MediaAsset(
                name=f"Generated {generated_image.provider_name} {width}x{height}",
                description=f"Generated from prompt: {prompt}",
                media_type=MediaType.IMAGE,
                url="",  # Will be set by provider
                dimensions=MediaDimensions(width=width, height=height),
                metadata=MediaMetadata(
                    file_size=len(generated_image.content) if isinstance(generated_image.content, bytes) else 0,
                    format=generated_image.format,
                ),
            )
            
            # Add custom generation tags
            asset.add_tag("generated")
            asset.add_tag(f"generated-{generated_image.provider_name}")
            
            # Determine which library to use
            target_library_id = library_id
            if not target_library_id:
                # Use or create default library
                if "default" not in self.libraries:
                    default_lib = self.create_library(
                        name="Default",
                        description="Default media library",
                    )
                    target_library_id = default_lib.library_id
                else:
                    target_library_id = "default"
            
            # Add asset to library
            added_asset = self.add_asset_to_library(target_library_id, asset)
            
            if added_asset:
                logger.info(
                    f"Generated and stored asset {added_asset.asset_id} "
                    f"using {generated_image.provider_name}"
                )
                return added_asset
            else:
                logger.error(f"Failed to add generated asset to library {target_library_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating asset: {e}", exc_info=True)
            return None
    
    def generate_variants_from_prompt(
        self,
        prompt: str,
        sizes: Optional[List[Tuple[int, int]]] = None,
        format_hint: Optional[str] = None,
        library_id: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """
        Generate multiple variants of an image across different sizes.
        
        Creates variants from a prompt with automatic provider fallback.
        Each variant is stored as a separate MediaAsset with appropriate tags.
        
        Args:
            prompt: Text description of image to generate
            sizes: List of (width, height) tuples. Default: [(512, 512), (1024, 1024), (512, 1024), (1024, 512)]
            format_hint: Optional format hint (e.g., 'square', 'vertical', 'horizontal')
            library_id: Library to add variants to (optional, uses default)
            **kwargs: Provider-specific options
            
        Returns:
            List of asset_ids for created variants
        """
        import asyncio
        
        # Default sizes if not specified
        if not sizes:
            sizes = [(512, 512), (1024, 1024), (512, 1024), (1024, 512)]
        
        variant_ids = []
        
        try:
            for width, height in sizes:
                # Generate asset for this size using async method
                asset = asyncio.run(
                    self.generate_asset_from_prompt(
                        prompt=prompt,
                        width=width,
                        height=height,
                        library_id=library_id,
                        **kwargs,
                    )
                )
                
                if asset:
                    # Add variant-specific tags
                    asset.add_tag(f"variant-{width}x{height}")
                    if format_hint:
                        asset.add_tag(f"format-{format_hint}")
                    
                    variant_ids.append(asset.asset_id)
                    logger.info(
                        f"Generated variant {asset.asset_id} "
                        f"for size {width}x{height}"
                    )
                else:
                    logger.warning(
                        f"Failed to generate variant for size {width}x{height}"
                    )
        
        except Exception as e:
            logger.error(f"Error generating variants: {e}", exc_info=True)
        
        return variant_ids
    
    def generate_variants_from_asset(
        self,
        asset_id: str,
        sizes: Optional[List[Tuple[int, int]]] = None,
        **kwargs,
    ) -> List[str]:
        """
        Generate multiple variants of an existing asset across different sizes.
        
        Uses original asset's prompt, tags, and metadata to create variants.
        Each variant is stored as a separate MediaAsset with proper linking.
        
        Args:
            asset_id: Original asset to base variants on
            sizes: List of (width, height) tuples. Default: [(512, 512), (1024, 1024), (512, 1024), (1024, 512)]
            **kwargs: Provider-specific options
            
        Returns:
            List of asset_ids for created variants
        """
        # Get original asset
        asset = self.assets.get(asset_id)
        if not asset:
            logger.error(f"Asset {asset_id} not found")
            return []
        
        # Extract prompt from description or tags
        prompt = asset.description or f"Asset variant of {asset.name}"
        
        # Find library for original asset
        library_id = None
        for lib_id, lib in self.libraries.items():
            if any(a.asset_id == asset_id for a in lib.assets.values()):
                library_id = lib_id
                break
        
        # Generate variants using prompt-based method
        variant_ids = self.generate_variants_from_prompt(
            prompt=prompt,
            sizes=sizes,
            format_hint=None,
            library_id=library_id,
            **kwargs,
        )
        
        # Tag variants as derived from original
        for variant_id in variant_ids:
            variant_asset = self.assets.get(variant_id)
            if variant_asset:
                variant_asset.add_tag(f"derived-from-{asset_id[:8]}")
        
        logger.info(
            f"Generated {len(variant_ids)} variants from asset {asset_id}"
        )
        
        return variant_ids
    
    async def export_asset_to_figma(
        self,
        asset_id: str,
        file_key: str,
        page_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Export media asset to Figma design file.
        
        Steps:
        1. Get asset from library
        2. Get Figma provider from chain
        3. Call export_to_figma() with fallback
        4. Store export info in asset tags
        5. Return export result
        
        Args:
            asset_id: Asset to export
            file_key: Figma file key
            page_id: Figma page ID (optional)
            **kwargs: Provider-specific options (frame_name, position, etc)
            
        Returns:
            Export metadata dict with figma_node_id and figma_url, or None on failure
        """
        try:
            from ..gateways.factory import get_media_generator_chain
            
            # Get asset
            asset = self.assets.get(asset_id)
            if not asset:
                logger.error(f"Asset {asset_id} not found")
                return None
            
            # Create a dummy GeneratedImage from the asset for export
            # (In production, would use actual binary/url)
            from ..media.generators.provider_chain import GeneratedImage
            
            generated_image = GeneratedImage(
                content=asset.name,
                content_type="binary",
                format="png" if asset.metadata and asset.metadata.format else "png",
                width=asset.dimensions.width if asset.dimensions else 1024,
                height=asset.dimensions.height if asset.dimensions else 1024,
                metadata={"asset_id": asset_id, "asset_name": asset.name},
                provider_name="exported_from_library",
            )
            
            # Get the provider chain
            chain = get_media_generator_chain()
            if not chain:
                logger.error("Failed to get media generator chain")
                return None
            
            # Export with provider fallback
            export_result = await chain.execute_export_figma(
                image=generated_image,
                file_key=file_key,
                page_id=page_id,
                **kwargs,
            )
            
            if not export_result:
                logger.error("All Figma export providers failed")
                return None
            
            # Store export info as tags in asset
            asset.add_tag(f"figma_exported")
            asset.add_category(f"figma_file_{file_key[:8]}")
            
            # Return export info
            result = {
                "figma_node_id": export_result.figma_node_id,
                "figma_url": export_result.figma_url,
                "figma_file_key": export_result.figma_file_key,
                "page_id": export_result.page_id,
                "asset_id": asset_id,
            }
            
            logger.info(f"Successfully exported asset {asset_id} to Figma")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting to Figma: {e}", exc_info=True)
            return None
    
    def apply_carousel_to_figma(
        self,
        template_config,  # FigmaTemplateConfig
        asset_ids_by_slot: Dict[str, str],
        texts_by_slot: Dict[str, str],
    ) -> Optional[Dict]:
        """
        Apply carousel template to Figma with generated assets.
        
        High-level helper that:
        1. Loads assets from library
        2. Uses FigmaTemplateEngine to apply template
        3. Returns export metadata
        
        Args:
            template_config: FigmaTemplateConfig with frame/text mappings
            asset_ids_by_slot: Dict mapping slot names to asset_ids
            texts_by_slot: Dict mapping text slot names to content strings
            
        Returns:
            Dict with template_application_id and export metadata, or None on failure
        """
        try:
            from .figma_templates import FigmaTemplateEngine
            
            # Create template engine
            engine = FigmaTemplateEngine(media_engine=self)
            
            # Load assets from library
            assets_dict = {}
            for slot_name, asset_id in asset_ids_by_slot.items():
                asset = self.assets.get(asset_id)
                if asset:
                    assets_dict[slot_name] = asset
                else:
                    logger.warning(f"Asset {asset_id} not found for slot {slot_name}")
            
            # Apply template
            application = engine.apply_carousel_template(
                template=template_config,
                assets=assets_dict,
                texts=texts_by_slot,
                export=True,
            )
            
            if not application:
                logger.error("Failed to apply carousel template")
                return None
            
            # Build result
            result = {
                "template_application_id": application.application_id,
                "template_name": application.template_name,
                "file_key": application.file_key,
                "export_url": application.export_url,
                "node_ids": application.node_ids,
                "status": application.status,
            }
            
            logger.info(
                f"Applied carousel template {application.application_id} "
                f"to {application.file_key}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying carousel to Figma: {e}", exc_info=True)
            return None
    
    def generate_video_from_prompt(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        duration_seconds: int = 10,
        library_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Generate a video asset from a text prompt.
        
        Creates a video using the video_generator ProviderChain with automatic fallback.
        Wraps result in MediaAsset and stores in library.
        
        Args:
            prompt: Text description of video to generate
            aspect_ratio: Video aspect ratio (9:16, 16:9, 1:1)
            duration_seconds: Video duration in seconds (5-120)
            library_id: Library to add video to (optional, uses default)
            **kwargs: Provider-specific options
            
        Returns:
            Asset ID of generated video, or None on failure
        """
        try:
            from ..gateways.factory import get_video_generator_chain
            from .models import MediaDimensions, MediaMetadata
            
            # Get the video generator chain
            chain = get_video_generator_chain()
            if not chain:
                logger.error("Failed to get video generator chain")
                return None
            
            # Call chain to generate video
            video_result = None
            
            # Try to generate using provider chain
            for provider in chain.providers:
                try:
                    if hasattr(provider, 'generate_video'):
                        video_result = provider.generate_video(
                            prompt=prompt,
                            aspect_ratio=aspect_ratio,
                            duration_seconds=duration_seconds,
                            **kwargs,
                        )
                        if video_result:
                            logger.info(f"Generated video using {provider.get_name()}")
                            break
                except Exception as e:
                    logger.debug(f"Provider {provider.get_name()} failed: {e}")
                    continue
            
            if not video_result:
                logger.error("All video generation providers failed")
                return None
            
            # Create MediaAsset from video
            asset = MediaAsset(
                name=f"Generated Video {aspect_ratio}",
                description=f"Generated from prompt: {prompt}",
                media_type=MediaType.VIDEO,
                url=video_result.get("url", ""),
                dimensions=MediaDimensions(
                    width=video_result.get("width", 720),
                    height=video_result.get("height", 1280),
                ),
                metadata=MediaMetadata(
                    format=video_result.get("format", "mp4"),
                    duration_seconds=video_result.get("duration", duration_seconds),
                ),
            )
            
            # Add generation tags
            asset.add_tag("generated")
            asset.add_tag(f"generated-video")
            asset.add_tag(f"aspect-{aspect_ratio.replace(':', '-')}")
            
            # Determine target library
            target_library_id = library_id
            if not target_library_id:
                if "default" not in self.libraries:
                    default_lib = self.create_library(
                        name="Default",
                        description="Default media library",
                    )
                    target_library_id = default_lib.library_id
                else:
                    target_library_id = "default"
            
            # Add asset to library
            added_asset = self.add_asset_to_library(target_library_id, asset)
            
            if added_asset:
                logger.info(
                    f"Generated and stored video asset {added_asset.asset_id} "
                    f"({aspect_ratio}, {duration_seconds}s)"
                )
                return added_asset.asset_id
            else:
                logger.error(f"Failed to add video asset to library {target_library_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating video: {e}", exc_info=True)
            return None


def get_media_engine() -> MediaEngine:
    """Get or create global media engine singleton."""
    global _media_engine
    if _media_engine is None:
        _media_engine = MediaEngine()
    return _media_engine


def reset_media_engine() -> None:
    """Reset media engine (for testing)."""
    global _media_engine
    _media_engine = None


# Convenience functions
def create_library(
    name: str,
    description: str = "",
    owner: str = "",
) -> MediaLibrary:
    """Create a new media library."""
    return get_media_engine().create_library(name, description, owner)


def add_asset(
    library_id: str,
    asset: MediaAsset,
) -> Optional[MediaAsset]:
    """Add asset to library."""
    return get_media_engine().add_asset_to_library(library_id, asset)


def track_performance(
    asset_id: str,
    campaign_id: str,
    channel: str,
    impressions: int = 0,
    clicks: int = 0,
    engagements: int = 0,
    conversions: int = 0,
    shares: int = 0,
    comments: int = 0,
) -> MediaPerformance:
    """Track asset performance."""
    return get_media_engine().track_asset_performance(
        asset_id, campaign_id, channel,
        impressions, clicks, engagements, conversions, shares, comments
    )


def get_performance(asset_id: str) -> List[MediaPerformance]:
    """Get asset performance records."""
    return get_media_engine().get_asset_performance(asset_id)


def suggest_optimization(
    asset_id: str,
    optimization_type: str,
    description: str,
    estimated_improvement: float = 0.0,
) -> MediaOptimizationSuggestion:
    """Create optimization suggestion."""
    return get_media_engine().suggest_optimization(
        asset_id, optimization_type, description, estimated_improvement
    )
