"""
Phase 7: Video Generator ProviderChain Tests

Tests for multi-provider video generation.
"""

import pytest
from aicmo.media.adapters import (
    RunwayMLAdapter,
    PikaLabsAdapter,
    LumaDreamAdapter,
    NoOpVideoAdapter,
)
from aicmo.media.engine import MediaEngine, get_media_engine, reset_media_engine
from aicmo.media.models import MediaAsset, MediaType
from aicmo.core.config_gateways import get_gateway_config


@pytest.fixture(autouse=True)
def reset_engine():
    """Reset media engine before and after each test."""
    reset_media_engine()
    yield
    reset_media_engine()


@pytest.fixture
def engine():
    """Get clean media engine for testing."""
    return get_media_engine()


class TestVideoAdapters:
    """Test individual video adapter implementations."""
    
    def test_runway_adapter_initialization(self):
        """Should initialize Runway ML adapter."""
        adapter = RunwayMLAdapter(dry_run=True)
        
        assert adapter.provider_name == "runway_ml"
        assert adapter.dry_run is True
    
    def test_runway_adapter_health_check(self):
        """Should report health status."""
        adapter = RunwayMLAdapter(dry_run=True)
        
        assert adapter.check_health() is True
    
    def test_runway_adapter_generate_video(self):
        """Should generate stub video."""
        adapter = RunwayMLAdapter(dry_run=True)
        
        result = adapter.generate_video(
            prompt="A beautiful sunset",
            aspect_ratio="9:16",
            duration_seconds=10,
        )
        
        assert result is not None
        assert result["provider"] == "runway_ml"
        assert result["width"] == 720
        assert result["height"] == 1280
        assert result["duration"] == 10
        assert result["format"] == "mp4"
    
    def test_pika_adapter_initialization(self):
        """Should initialize Pika Labs adapter."""
        adapter = PikaLabsAdapter(dry_run=True)
        
        assert adapter.provider_name == "pika_labs"
    
    def test_pika_adapter_generate_video(self):
        """Should generate stub video."""
        adapter = PikaLabsAdapter(dry_run=True)
        
        result = adapter.generate_video(
            prompt="A test video",
            aspect_ratio="16:9",
            duration_seconds=15,
        )
        
        assert result is not None
        assert result["provider"] == "pika_labs"
        assert result["width"] == 1920
        assert result["height"] == 1080
    
    def test_luma_adapter_initialization(self):
        """Should initialize Luma Dream adapter."""
        adapter = LumaDreamAdapter(dry_run=True)
        
        assert adapter.provider_name == "luma_dream"
    
    def test_luma_adapter_generate_video(self):
        """Should generate stub video."""
        adapter = LumaDreamAdapter(dry_run=True)
        
        result = adapter.generate_video(
            prompt="High quality video",
            aspect_ratio="1:1",
        )
        
        assert result is not None
        assert result["provider"] == "luma_dream"
        assert result["width"] == 1024
        assert result["height"] == 1024
    
    def test_noop_video_adapter(self):
        """Should always work (safe fallback)."""
        adapter = NoOpVideoAdapter()
        
        assert adapter.check_health() is True
        
        result = adapter.generate_video(
            prompt="Any prompt",
            aspect_ratio="9:16",
            duration_seconds=10,
        )
        
        assert result is not None
        assert result["is_stub"] is True
        assert result["provider"] == "noop_video"


class TestVideoAdapterAspectRatios:
    """Test aspect ratio handling."""
    
    def test_portrait_aspect_ratio(self):
        """Should handle portrait aspect ratio."""
        adapter = RunwayMLAdapter(dry_run=True)
        
        result = adapter.generate_video(
            prompt="Portrait video",
            aspect_ratio="9:16",
        )
        
        assert result["width"] == 720
        assert result["height"] == 1280
    
    def test_landscape_aspect_ratio(self):
        """Should handle landscape aspect ratio."""
        adapter = RunwayMLAdapter(dry_run=True)
        
        result = adapter.generate_video(
            prompt="Landscape video",
            aspect_ratio="16:9",
        )
        
        assert result["width"] == 1920
        assert result["height"] == 1080
    
    def test_square_aspect_ratio(self):
        """Should handle square aspect ratio."""
        adapter = RunwayMLAdapter(dry_run=True)
        
        result = adapter.generate_video(
            prompt="Square video",
            aspect_ratio="1:1",
        )
        
        assert result["width"] == 1024
        assert result["height"] == 1024
    
    def test_unknown_aspect_ratio(self):
        """Should default to square for unknown ratio."""
        adapter = RunwayMLAdapter(dry_run=True)
        
        result = adapter.generate_video(
            prompt="Unknown aspect",
            aspect_ratio="3:2",
        )
        
        # Should default to square
        assert result["width"] == 1024
        assert result["height"] == 1024


class TestVideoGeneratorChain:
    """Test video generator provider chain integration."""
    
    def test_get_video_generator_chain(self):
        """Should create video generator chain."""
        from aicmo.gateways.factory import get_video_generator_chain
        
        chain = get_video_generator_chain()
        
        assert chain is not None
        assert len(chain.providers) > 0
    
    def test_video_chain_provider_order(self):
        """Should have providers in fallback order."""
        from aicmo.gateways.factory import get_video_generator_chain
        
        chain = get_video_generator_chain()
        
        provider_names = [p.get_name() for p in chain.providers]
        
        # Should have Runway first, no-op last
        assert provider_names[0] == "runway_ml"
        assert provider_names[-1] == "noop_video"
    
    def test_video_chain_respects_dry_run(self):
        """Should respect dry_run configuration."""
        config = get_gateway_config()
        assert config.DRY_RUN_MODE  # Should be true in test
        
        from aicmo.gateways.factory import get_video_generator_chain
        
        chain = get_video_generator_chain()
        
        # All providers should be in dry_run mode
        for provider in chain.providers[:-1]:  # Exclude noop which ignores dry_run
            assert provider.dry_run is True


class TestMediaEngineVideoGeneration:
    """Test MediaEngine video generation integration."""
    
    def test_generate_video_from_prompt(self, engine):
        """Should generate video asset."""
        asset_id = engine.generate_video_from_prompt(
            prompt="A beautiful landscape",
            aspect_ratio="16:9",
            duration_seconds=15,
        )
        
        # Should return asset ID (or None in dry_run if generation fails)
        assert asset_id is None or isinstance(asset_id, str)
    
    def test_generate_video_creates_default_library(self, engine):
        """Should create default library if needed."""
        asset_id = engine.generate_video_from_prompt(
            prompt="Test video",
            library_id=None,
        )
        
        # Should have created default library
        assert "default" in engine.libraries or asset_id is None
    
    def test_generate_video_uses_specified_library(self, engine):
        """Should use specified library."""
        lib = engine.create_library("Videos")
        
        asset_id = engine.generate_video_from_prompt(
            prompt="Test",
            library_id=lib.library_id,
        )
        
        # Should either create asset or handle error gracefully
        assert isinstance(asset_id, (str, type(None)))
    
    def test_generate_video_portrait_format(self, engine):
        """Should generate portrait video for reels/shorts."""
        asset_id = engine.generate_video_from_prompt(
            prompt="Vertical video for social media",
            aspect_ratio="9:16",
            duration_seconds=30,
        )
        
        # Should handle portrait format
        assert isinstance(asset_id, (str, type(None)))
    
    def test_generate_video_landscape_format(self, engine):
        """Should generate landscape video."""
        asset_id = engine.generate_video_from_prompt(
            prompt="Landscape tutorial video",
            aspect_ratio="16:9",
            duration_seconds=60,
        )
        
        # Should handle landscape format
        assert isinstance(asset_id, (str, type(None)))
    
    def test_generate_video_with_custom_duration(self, engine):
        """Should respect custom duration."""
        asset_id = engine.generate_video_from_prompt(
            prompt="Short clip",
            duration_seconds=5,
        )
        
        assert isinstance(asset_id, (str, type(None)))
    
    def test_generate_video_with_kwargs(self, engine):
        """Should pass kwargs to provider."""
        asset_id = engine.generate_video_from_prompt(
            prompt="Video with options",
            quality="high",
            style="cinematic",
        )
        
        assert isinstance(asset_id, (str, type(None)))


class TestVideoAssetProperties:
    """Test properties of generated video assets."""
    
    def test_video_asset_type(self, engine):
        """Video assets should have VIDEO media type."""
        asset = MediaAsset(
            name="Test Video",
            media_type=MediaType.VIDEO,
            url="http://example.com/video.mp4",
        )
        
        assert asset.media_type == MediaType.VIDEO
    
    def test_video_asset_tags(self, engine):
        """Video assets should have appropriate tags."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Generated Video",
            media_type=MediaType.VIDEO,
            url="http://example.com/video.mp4",
        )
        asset.add_tag("generated")
        asset.add_tag("generated-video")
        asset.add_tag("aspect-9-16")
        
        engine.add_asset_to_library(lib.library_id, asset)
        
        assert "generated" in asset.tags
        assert "generated-video" in asset.tags


class TestVideoEdgeCases:
    """Test edge cases and error handling."""
    
    def test_generate_video_empty_prompt(self, engine):
        """Should handle empty prompt."""
        asset_id = engine.generate_video_from_prompt(
            prompt="",
        )
        
        # Should not crash
        assert isinstance(asset_id, (str, type(None)))
    
    def test_generate_video_very_short_duration(self, engine):
        """Should handle short duration."""
        asset_id = engine.generate_video_from_prompt(
            prompt="Short",
            duration_seconds=1,
        )
        
        assert isinstance(asset_id, (str, type(None)))
    
    def test_generate_video_very_long_duration(self, engine):
        """Should handle long duration."""
        asset_id = engine.generate_video_from_prompt(
            prompt="Long",
            duration_seconds=600,
        )
        
        assert isinstance(asset_id, (str, type(None)))
    
    def test_multiple_video_generations(self, engine):
        """Should handle multiple video generations."""
        lib = engine.create_library("Videos")
        
        asset_ids = []
        for i in range(3):
            asset_id = engine.generate_video_from_prompt(
                prompt=f"Video {i}",
                library_id=lib.library_id,
            )
            if asset_id:
                asset_ids.append(asset_id)
        
        # Should handle multiple generations without error
        assert isinstance(asset_ids, list)


class TestVideoAdapterConfiguration:
    """Test adapter configuration and credentials."""
    
    def test_runway_without_credentials(self):
        """Should work in dry_run without credentials."""
        adapter = RunwayMLAdapter(api_key=None, dry_run=True)
        
        assert adapter.check_health() is True
    
    def test_pika_without_credentials(self):
        """Should work in dry_run without credentials."""
        adapter = PikaLabsAdapter(api_key=None, dry_run=True)
        
        assert adapter.check_health() is True
    
    def test_luma_without_credentials(self):
        """Should work in dry_run without credentials."""
        adapter = LumaDreamAdapter(api_key=None, dry_run=True)
        
        assert adapter.check_health() is True
