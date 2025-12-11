"""Phase 4: Media Management System Tests.

Tests for media asset lifecycle, library management, performance tracking,
and optimization suggestions.
"""

import pytest
from datetime import datetime
from aicmo.media import (
    MediaType,
    ImageFormat,
    VideoFormat,
    MediaStatus,
    MediaDimensions,
    MediaMetadata,
    MediaAsset,
    MediaVariant,
    MediaLibrary,
    MediaPerformance,
    MediaOptimizationSuggestion,
    MediaEngine,
    get_media_engine,
    reset_media_engine,
    create_library,
    add_asset,
    track_performance,
    get_performance,
    suggest_optimization,
)


# ============================================================================
# Test MediaType and Format Enums
# ============================================================================

class TestMediaEnums:
    """Test media type and format enumerations."""
    
    def test_media_type_enum(self):
        """Test MediaType enum values."""
        assert MediaType.IMAGE.value == "image"
        assert MediaType.VIDEO.value == "video"
        assert MediaType.GIF.value == "gif"
        assert MediaType.INFOGRAPHIC.value == "infographic"
        assert MediaType.THUMBNAIL.value == "thumbnail"
        assert MediaType.BANNER.value == "banner"
        assert MediaType.ICON.value == "icon"
    
    def test_image_format_enum(self):
        """Test ImageFormat enum values."""
        assert ImageFormat.JPEG.value == "jpeg"
        assert ImageFormat.PNG.value == "png"
        assert ImageFormat.GIF.value == "gif"
        assert ImageFormat.WEBP.value == "webp"
        assert ImageFormat.SVG.value == "svg"
    
    def test_video_format_enum(self):
        """Test VideoFormat enum values."""
        assert VideoFormat.MP4.value == "mp4"
        assert VideoFormat.WEBM.value == "webm"
        assert VideoFormat.MOV.value == "mov"
        assert VideoFormat.MKV.value == "mkv"
    
    def test_media_status_enum(self):
        """Test MediaStatus enum values."""
        assert MediaStatus.DRAFT.value == "draft"
        assert MediaStatus.APPROVED.value == "approved"
        assert MediaStatus.PUBLISHED.value == "published"
        assert MediaStatus.ARCHIVED.value == "archived"
        assert MediaStatus.DELETED.value == "deleted"


# ============================================================================
# Test MediaDimensions
# ============================================================================

class TestMediaDimensions:
    """Test MediaDimensions model."""
    
    def test_dimensions_creation(self):
        """Test creating media dimensions."""
        dims = MediaDimensions(width=1920, height=1080)
        assert dims.width == 1920
        assert dims.height == 1080
    
    def test_dimensions_aspect_ratio(self):
        """Test aspect ratio calculation."""
        # 16:9
        dims = MediaDimensions(width=1920, height=1080)
        assert dims.aspect_ratio() == pytest.approx(16 / 9, rel=0.01)
        
        # 1:1
        dims = MediaDimensions(width=1000, height=1000)
        assert dims.aspect_ratio() == pytest.approx(1.0, rel=0.01)
        
        # 4:3
        dims = MediaDimensions(width=800, height=600)
        assert dims.aspect_ratio() == pytest.approx(4 / 3, rel=0.01)
    
    def test_dimensions_string(self):
        """Test string representation."""
        dims = MediaDimensions(width=1920, height=1080)
        assert str(dims) == "1920x1080"
    
    def test_dimensions_zero_height(self):
        """Test aspect ratio with zero height (edge case)."""
        dims = MediaDimensions(width=1920, height=0)
        assert dims.aspect_ratio() == 0.0


# ============================================================================
# Test MediaMetadata
# ============================================================================

class TestMediaMetadata:
    """Test MediaMetadata model."""
    
    def test_metadata_creation(self):
        """Test creating media metadata."""
        meta = MediaMetadata(
            file_size=1024000,
            duration=30,
            format="mp4",
            bitrate=3000
        )
        assert meta.file_size == 1024000
        assert meta.duration == 30
        assert meta.bitrate == 3000
    
    def test_metadata_file_size_mb(self):
        """Test file size in megabytes."""
        meta = MediaMetadata(
            file_size=1048576,  # 1 MB in bytes
            duration=30,
            format="mp4"
        )
        assert meta.file_size_mb() == pytest.approx(1.0, rel=0.01)
    
    def test_metadata_optional_fields(self):
        """Test metadata with optional fields."""
        meta = MediaMetadata(
            file_size=500000,
            duration=None,
            bitrate=None
        )
        assert meta.file_size == 500000
        assert meta.duration is None
        assert meta.bitrate is None


# ============================================================================
# Test MediaAsset
# ============================================================================

class TestMediaAsset:
    """Test MediaAsset model."""
    
    def test_asset_creation(self):
        """Test creating a media asset."""
        asset = MediaAsset(
            name="promo_image.png",
            media_type=MediaType.IMAGE,
            content_hash="abc123",
            dimensions=MediaDimensions(width=1920, height=1080),
            metadata=MediaMetadata(
                file_size=500000,
                duration=0,
                format="png"
            )
        )
        assert asset.name == "promo_image.png"
        assert asset.media_type == MediaType.IMAGE
        assert asset.status == MediaStatus.DRAFT
        assert asset.is_approved is False
    
    def test_asset_upload_date(self):
        """Test asset upload date is set."""
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash1",
            dimensions=MediaDimensions(width=100, height=100),
            metadata=MediaMetadata(
                file_size=1000,
                duration=0,
                format="png"
            )
        )
        assert asset.uploaded_at is not None
        assert isinstance(asset.uploaded_at, datetime)
    
    def test_asset_video(self):
        """Test creating video asset."""
        asset = MediaAsset(
            name="video.mp4",
            media_type=MediaType.VIDEO,
            content_hash="video_hash",
            dimensions=MediaDimensions(width=1920, height=1080),
            metadata=MediaMetadata(
                file_size=5000000,
                duration=60,
                format="mp4",
                bitrate=8000
            )
        )
        assert asset.media_type == MediaType.VIDEO
        assert asset.metadata.duration == 60
    
    def test_asset_tags(self):
        """Test asset tagging."""
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash",
            dimensions=MediaDimensions(width=100, height=100),
            metadata=MediaMetadata(file_size=1000, duration=0, format="png"),
            tags={"campaign", "summer"}
        )
        assert "campaign" in asset.tags
        assert "summer" in asset.tags
    
    def test_asset_add_tag(self):
        """Test adding tags to asset."""
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash"
        )
        asset.add_tag("promotional")
        assert "promotional" in asset.tags
    
    def test_asset_add_category(self):
        """Test adding categories to asset."""
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash"
        )
        asset.add_category("Email")
        assert "email" in asset.categories
    
    def test_asset_approval(self):
        """Test asset approval workflow."""
        asset = MediaAsset(name="test.png", media_type=MediaType.IMAGE)
        assert asset.is_approved is False
        assert asset.status == MediaStatus.DRAFT
        
        asset.approve(notes="Ready for production")
        assert asset.is_approved is True
        assert asset.status == MediaStatus.APPROVED
        assert asset.approval_notes == "Ready for production"
    
    def test_asset_mark_used(self):
        """Test marking asset as used."""
        asset = MediaAsset(name="test.png", media_type=MediaType.IMAGE)
        assert asset.usage_count == 0
        
        asset.mark_used("campaign_1")
        assert asset.usage_count == 1
        assert "campaign_1" in asset.campaigns_used_in
        assert asset.last_used_at is not None


# ============================================================================
# Test MediaVariant
# ============================================================================

class TestMediaVariant:
    """Test MediaVariant model."""
    
    def test_variant_creation(self):
        """Test creating media variant."""
        variant = MediaVariant(
            asset_id="asset_123",
            name="thumbnail",
            dimensions=MediaDimensions(width=300, height=300),
            file_size=50000
        )
        assert variant.asset_id == "asset_123"
        assert variant.name == "thumbnail"
    
    def test_variant_multiple_formats(self):
        """Test creating multiple variants for same asset."""
        asset_id = "video_456"
        
        thumbnail = MediaVariant(
            asset_id=asset_id,
            name="thumbnail",
            dimensions=MediaDimensions(width=300, height=300),
            file_size=50000
        )
        
        preview = MediaVariant(
            asset_id=asset_id,
            name="preview",
            dimensions=MediaDimensions(width=640, height=360),
            file_size=200000
        )
        
        assert thumbnail.asset_id == preview.asset_id
        assert thumbnail.name != preview.name


# ============================================================================
# Test MediaLibrary
# ============================================================================

class TestMediaLibrary:
    """Test MediaLibrary model and operations."""
    
    def test_library_creation(self):
        """Test creating media library."""
        library = MediaLibrary(
            name="Marketing Assets",
            description="All marketing campaign assets"
        )
        assert library.name == "Marketing Assets"
        assert len(library.assets) == 0
    
    def test_library_add_asset(self):
        """Test adding assets to library."""
        library = MediaLibrary(name="Test Library")
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash1",
            dimensions=MediaDimensions(width=100, height=100),
            metadata=MediaMetadata(file_size=1000, duration=0, format="png")
        )
        
        library.add_asset(asset)
        assert len(library.assets) == 1
        assert asset.asset_id in library.assets
    
    def test_library_remove_asset(self):
        """Test removing assets from library."""
        library = MediaLibrary(name="Test Library")
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash1",
            metadata=MediaMetadata(file_size=1000, duration=0, format="png")
        )
        
        library.add_asset(asset)
        assert len(library.assets) == 1
        
        library.remove_asset(asset.asset_id)
        assert len(library.assets) == 0
    
    def test_library_get_asset(self):
        """Test retrieving asset from library."""
        library = MediaLibrary(name="Test Library")
        asset = MediaAsset(name="test.png", media_type=MediaType.IMAGE)
        
        library.add_asset(asset)
        retrieved = library.get_asset(asset.asset_id)
        assert retrieved is not None
        assert retrieved.name == "test.png"
    
    def test_library_asset_search_by_tag(self):
        """Test searching assets in library by tag."""
        library = MediaLibrary(name="Search Test")
        
        # Add assets with different tags
        asset1 = MediaAsset(
            name="summer_promo.png",
            media_type=MediaType.IMAGE,
            content_hash="hash1",
            tags={"summer", "promo"}
        )
        
        asset2 = MediaAsset(
            name="winter_sale.png",
            media_type=MediaType.IMAGE,
            content_hash="hash2",
            tags={"winter", "sale"}
        )
        
        library.add_asset(asset1)
        library.add_asset(asset2)
        
        # Find assets by tag
        summer_assets = library.get_assets_by_tag("summer")
        assert len(summer_assets) == 1
        assert summer_assets[0].name == "summer_promo.png"
    
    def test_library_get_most_used_assets(self):
        """Test getting most reused assets."""
        library = MediaLibrary(name="Usage Test")
        
        asset1 = MediaAsset(name="popular.png", media_type=MediaType.IMAGE)
        asset2 = MediaAsset(name="unpopular.png", media_type=MediaType.IMAGE)
        
        asset1.usage_count = 10
        asset2.usage_count = 2
        
        library.add_asset(asset1)
        library.add_asset(asset2)
        
        most_used = library.get_most_used_assets(limit=1)
        assert len(most_used) == 1
        assert most_used[0].name == "popular.png"
    
    def test_library_total_size_mb(self):
        """Test library total size calculation."""
        library = MediaLibrary(name="Size Test")
        
        # Add asset with 1 MB
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            metadata=MediaMetadata(file_size=1048576, duration=0, format="png")
        )
        library.add_asset(asset)
        
        assert library.total_size_mb() == pytest.approx(1.0, rel=0.01)
    
    def test_library_asset_count(self):
        """Test asset count."""
        library = MediaLibrary(name="Count Test")
        
        for i in range(3):
            asset = MediaAsset(
                name=f"image{i}.png",
                media_type=MediaType.IMAGE
            )
            library.add_asset(asset)
        
        assert library.asset_count() == 3


# ============================================================================
# Test MediaPerformance
# ============================================================================

class TestMediaPerformance:
    """Test MediaPerformance tracking."""
    
    def test_performance_creation(self):
        """Test creating performance metrics."""
        perf = MediaPerformance(
            asset_id="asset_123",
            channel="email",
            impressions=1000,
            clicks=50,
            engagements=75
        )
        assert perf.asset_id == "asset_123"
        assert perf.channel == "email"
        assert perf.impressions == 1000
    
    def test_performance_click_through_rate(self):
        """Test CTR calculation."""
        perf = MediaPerformance(
            asset_id="asset_1",
            channel="web",
            impressions=1000,
            clicks=50,
            engagements=60
        )
        perf.calculate_rates()
        assert perf.ctr == 0.05  # 50/1000
    
    def test_performance_engagement_rate(self):
        """Test engagement rate calculation."""
        perf = MediaPerformance(
            asset_id="asset_1",
            channel="social",
            impressions=1000,
            clicks=100,
            engagements=200
        )
        perf.calculate_rates()
        assert perf.engagement_rate == 0.2  # 200/1000
    
    def test_performance_conversion_metrics(self):
        """Test conversion tracking."""
        perf = MediaPerformance(
            asset_id="asset_1",
            channel="display",
            impressions=1000,
            clicks=100,
            engagements=80,
            conversions=20
        )
        perf.calculate_rates()
        assert perf.conversions == 20
        assert perf.conversion_rate == 0.2  # 20/100 clicks
    
    def test_performance_zero_impressions(self):
        """Test performance with zero impressions."""
        perf = MediaPerformance(
            asset_id="asset_1",
            channel="email",
            impressions=0,
            clicks=0,
            engagements=0
        )
        perf.calculate_rates()
        assert perf.ctr == 0
        assert perf.engagement_rate == 0
    
    def test_performance_high_performing(self):
        """Test high performing asset detection."""
        high_perf = MediaPerformance(
            asset_id="a1",
            channel="email",
            impressions=1000,
            clicks=60
        )
        high_perf.calculate_rates()
        assert high_perf.is_high_performing(ctr_threshold=0.05)
        
        low_perf = MediaPerformance(
            asset_id="a2",
            channel="email",
            impressions=1000,
            clicks=20
        )
        low_perf.calculate_rates()
        assert not low_perf.is_high_performing(ctr_threshold=0.05)


# ============================================================================
# Test MediaOptimizationSuggestion
# ============================================================================

class TestMediaOptimizationSuggestion:
    """Test optimization suggestions."""
    
    def test_suggestion_creation(self):
        """Test creating optimization suggestion."""
        suggestion = MediaOptimizationSuggestion(
            asset_id="asset_123",
            type="compress",
            description="Reduce file size to improve load time",
            priority="high"
        )
        assert suggestion.asset_id == "asset_123"
        assert suggestion.priority == "high"
        assert suggestion.is_applied is False
    
    def test_suggestion_different_types(self):
        """Test different suggestion types."""
        types = ["resize", "compress", "reformat", "remove_bg"]
        suggestions = [
            MediaOptimizationSuggestion(
                asset_id="a1",
                type=t,
                description=f"Try {t}",
                priority="medium"
            )
            for t in types
        ]
        
        assert len(suggestions) == 4
        assert suggestions[0].type == "resize"
        assert suggestions[3].type == "remove_bg"
    
    def test_suggestion_different_priorities(self):
        """Test different priority levels."""
        high = MediaOptimizationSuggestion(
            asset_id="a1", type="compress", description="Fix", priority="high"
        )
        medium = MediaOptimizationSuggestion(
            asset_id="a2", type="resize", description="Improve", priority="medium"
        )
        low = MediaOptimizationSuggestion(
            asset_id="a3", type="reformat", description="Consider", priority="low"
        )
        
        assert high.priority == "high"
        assert medium.priority == "medium"
        assert low.priority == "low"


# ============================================================================
# Test MediaEngine
# ============================================================================

class TestMediaEngine:
    """Test MediaEngine singleton."""
    
    def setup_method(self):
        """Reset engine before each test."""
        reset_media_engine()
    
    def test_engine_singleton(self):
        """Test MediaEngine is a singleton."""
        engine1 = get_media_engine()
        engine2 = get_media_engine()
        assert engine1 is engine2
    
    def test_engine_create_library(self):
        """Test creating library via engine."""
        engine = get_media_engine()
        library = engine.create_library(
            name="Test Library",
            description="Test description"
        )
        assert library.name == "Test Library"
        assert library.library_id in engine.libraries
    
    def test_engine_add_asset(self):
        """Test adding asset to library via engine."""
        engine = get_media_engine()
        library = engine.create_library(name="Test")
        
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash1",
            dimensions=MediaDimensions(width=100, height=100),
            metadata=MediaMetadata(file_size=1000, duration=0, format="png")
        )
        
        result = engine.add_asset_to_library(
            library_id=library.library_id,
            asset=asset
        )
        assert result is not None
        assert asset.asset_id in library.assets
    
    def test_engine_find_duplicates_by_hash(self):
        """Test finding duplicate assets by content hash."""
        engine = get_media_engine()
        
        # Create two assets with same hash
        asset1 = MediaAsset(
            name="image1.png",
            media_type=MediaType.IMAGE,
            content_hash="same_hash",
            dimensions=MediaDimensions(width=100, height=100),
            metadata=MediaMetadata(file_size=1000, duration=0, format="png")
        )
        
        asset2 = MediaAsset(
            name="image2.png",
            media_type=MediaType.IMAGE,
            content_hash="same_hash",
            dimensions=MediaDimensions(width=100, height=100),
            metadata=MediaMetadata(file_size=1000, duration=0, format="png")
        )
        
        engine.assets[asset1.asset_id] = asset1
        engine.assets[asset2.asset_id] = asset2
        
        # Find duplicates
        duplicates = engine.find_duplicate_assets("same_hash")
        assert len(duplicates) == 2
    
    def test_engine_track_performance(self):
        """Test tracking asset performance."""
        engine = get_media_engine()
        
        asset = MediaAsset(
            name="test.png",
            media_type=MediaType.IMAGE,
            content_hash="hash_perf"
        )
        engine.assets[asset.asset_id] = asset
        
        # Track performance
        perf = engine.track_asset_performance(
            asset_id=asset.asset_id,
            campaign_id="camp_1",
            channel="email",
            impressions=1000,
            clicks=50,
            engagements=60
        )
        
        assert perf.channel == "email"
        assert perf.impressions == 1000
    
    def test_engine_get_asset_performance(self):
        """Test getting asset performance."""
        engine = get_media_engine()
        
        asset = MediaAsset(name="test.png", media_type=MediaType.IMAGE)
        engine.assets[asset.asset_id] = asset
        
        # Track performance on multiple channels
        engine.track_asset_performance(asset.asset_id, "camp_1", "email", 1000, 50, 60)
        engine.track_asset_performance(asset.asset_id, "camp_1", "web", 2000, 100, 150)
        
        performance = engine.get_asset_performance(asset.asset_id)
        assert len(performance) == 2
    
    def test_engine_get_best_performers(self):
        """Test getting best performing assets by CTR."""
        engine = get_media_engine()
        
        # Create assets with different CTRs
        asset1 = MediaAsset(name="good.png", media_type=MediaType.IMAGE, content_hash="hash_good")
        asset2 = MediaAsset(name="bad.png", media_type=MediaType.IMAGE, content_hash="hash_bad")
        
        engine.assets[asset1.asset_id] = asset1
        engine.assets[asset2.asset_id] = asset2
        
        # Track performance - good CTR
        engine.track_asset_performance(asset1.asset_id, "camp_1", "email", 1000, 50, 60)
        # Track performance - poor CTR
        engine.track_asset_performance(asset2.asset_id, "camp_1", "email", 1000, 10, 15)
        
        best = engine.get_best_performing_assets("camp_1", limit=5)
        assert len(best) >= 1
        # First should be the good one
        assert best[0][0] == asset1.asset_id
    
    def test_engine_suggest_optimization(self):
        """Test creating optimization suggestion."""
        engine = get_media_engine()
        
        asset = MediaAsset(name="test.png", media_type=MediaType.IMAGE, content_hash="hash_opt")
        engine.assets[asset.asset_id] = asset
        
        suggestion = engine.suggest_optimization(
            asset_id=asset.asset_id,
            optimization_type="compress",
            description="Optimize for mobile",
            priority="high"
        )
        assert suggestion.asset_id == asset.asset_id
        assert suggestion.priority == "high"
        assert suggestion.is_applied is False
    
    def test_engine_auto_suggest_optimizations(self):
        """Test auto-generating suggestions based on performance."""
        engine = get_media_engine()
        
        # Create asset with VERY large file (>5MB)
        asset = MediaAsset(
            name="large.png",
            media_type=MediaType.IMAGE,
            content_hash="hash_large",
            dimensions=MediaDimensions(width=5000, height=5000),
            metadata=MediaMetadata(file_size=6000000, duration=0, format="png")  # 6MB, > 5MB threshold
        )
        
        engine.assets[asset.asset_id] = asset
        
        # Track LOW performance (should trigger refresh_design suggestion)
        engine.track_asset_performance(asset.asset_id, "camp_1", "web", 10000, 100, 150)
        
        # Get auto suggestions
        suggestions = engine.auto_suggest_optimizations(asset.asset_id)
        
        # Should suggest optimization for low-performing asset AND large file
        assert len(suggestions) >= 2
        assert any(s.type == "refresh_design" for s in suggestions)
        assert any(s.type == "compress" for s in suggestions)
    
    def test_engine_library_statistics(self):
        """Test getting library statistics."""
        engine = get_media_engine()
        library = engine.create_library(name="Stats Test")
        
        # Add multiple assets
        for i in range(3):
            asset = MediaAsset(
                name=f"image{i}.png",
                media_type=MediaType.IMAGE,
                content_hash=f"hash_{i}",
                dimensions=MediaDimensions(width=100, height=100),
                metadata=MediaMetadata(file_size=1000, duration=0, format="png")
            )
            engine.add_asset_to_library(library.library_id, asset)
        
        stats = engine.get_library_statistics(library.library_id)
        assert stats["asset_count"] == 3


# ============================================================================
# Test Integration Workflows
# ============================================================================

class TestMediaIntegration:
    """Integration tests for complete workflows."""
    
    def setup_method(self):
        """Reset engine before each test."""
        reset_media_engine()
    
    def test_complete_media_workflow(self):
        """Test complete media management workflow."""
        # Create library
        library = create_library(name="Campaign Assets", description="All campaign media")
        assert library.name == "Campaign Assets"
        
        # Create and add image asset
        image_asset = MediaAsset(
            name="banner.png",
            media_type=MediaType.IMAGE,
            content_hash="banner_hash_123",
            dimensions=MediaDimensions(width=1920, height=400),
            metadata=MediaMetadata(file_size=500000, duration=0, format="png"),
            tags={"campaign", "banner"}
        )
        image_result = add_asset(library.library_id, image_asset)
        assert image_result is not None
        image_id = image_result.asset_id
        
        # Create and add video asset
        video_asset = MediaAsset(
            name="promo.mp4",
            media_type=MediaType.VIDEO,
            content_hash="video_hash_456",
            dimensions=MediaDimensions(width=1920, height=1080),
            metadata=MediaMetadata(file_size=5000000, duration=30, format="mp4", bitrate=8000),
            tags={"campaign", "video"}
        )
        video_result = add_asset(library.library_id, video_asset)
        assert video_result is not None
        video_id = video_result.asset_id
        
        # Track performance across channels
        track_performance(image_id, "camp_1", "email", 5000, 250, 300)
        track_performance(image_id, "camp_1", "web", 10000, 400, 500)
        track_performance(video_id, "camp_1", "social", 50000, 2500, 4000)
        
        # Get performance metrics
        image_perf = get_performance(image_id)
        video_perf = get_performance(video_id)
        
        assert len(image_perf) == 2  # Email and web
        assert len(video_perf) == 1  # Social
    
    def test_media_library_management(self):
        """Test managing multiple libraries."""
        # Create multiple libraries
        summer_lib = create_library(name="Summer Campaign")
        winter_lib = create_library(name="Winter Campaign")
        
        # Add different assets to each
        summer_asset = MediaAsset(
            name="sun.png",
            media_type=MediaType.IMAGE,
            content_hash="summer_hash",
            tags={"summer"}
        )
        
        winter_asset = MediaAsset(
            name="snow.png",
            media_type=MediaType.IMAGE,
            content_hash="winter_hash",
            tags={"winter"}
        )
        
        summer_result = add_asset(summer_lib.library_id, summer_asset)
        winter_result = add_asset(winter_lib.library_id, winter_asset)
        
        # Verify separation
        assert summer_result.asset_id != winter_result.asset_id
    
    def test_duplicate_detection_workflow(self):
        """Test duplicate asset detection."""
        engine = get_media_engine()
        
        # Create two assets with same content hash
        asset1 = MediaAsset(
            name="original.png",
            media_type=MediaType.IMAGE,
            content_hash="duplicate_content"
        )
        
        asset2 = MediaAsset(
            name="copy.png",
            media_type=MediaType.IMAGE,
            content_hash="duplicate_content"
        )
        
        engine.assets[asset1.asset_id] = asset1
        engine.assets[asset2.asset_id] = asset2
        
        # Find duplicates
        duplicates = engine.find_duplicate_assets("duplicate_content")
        
        # Should identify the duplicate hash
        assert len(duplicates) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
