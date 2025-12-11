"""
Phase 4.5: Media Generator Provider Chain and Figma Integration Tests

Comprehensive test suite for:
- MediaGeneratorChain provider ordering and fallback
- Dry-run image generation across all providers
- Figma export functionality
- MediaEngine integration (generate_asset_from_prompt, export_asset_to_figma)
- Missing configuration handling
- Multi-provider failover scenarios
"""

import pytest
import asyncio
from typing import Optional

# Phase 4.5 imports
from aicmo.media.generators.provider_chain import (
    GeneratedImage,
    FigmaExportResult,
    MediaGeneratorProvider,
    MediaGeneratorChain,
)
from aicmo.media.adapters import (
    SDXLAdapter,
    OpenAIImagesAdapter,
    FluxAdapter,
    ReplicateSDXLAdapter,
    FigmaAPIAdapter,
    CanvaAPIAdapter,
    NoOpMediaAdapter,
)
from aicmo.media.engine import get_media_engine, reset_media_engine
from aicmo.media.models import MediaAsset, MediaType
from aicmo.gateways.factory import get_media_generator_chain


# ============================================================================
# Test 1: Provider Initialization & Health Checks
# ============================================================================

class TestProviderInitialization:
    """Test all providers can be instantiated and report health."""
    
    def test_sdxl_adapter_initialization(self):
        """SDXL adapter initializes correctly."""
        adapter = SDXLAdapter(dry_run=True)
        assert adapter.get_name() == "sdxl"
        assert asyncio.run(adapter.check_health()) is True
    
    def test_openai_images_adapter_initialization(self):
        """OpenAI Images adapter initializes correctly."""
        adapter = OpenAIImagesAdapter(dry_run=True)
        assert adapter.get_name() == "openai_images"
        assert asyncio.run(adapter.check_health()) is True
    
    def test_flux_adapter_initialization(self):
        """Flux adapter initializes correctly."""
        adapter = FluxAdapter(dry_run=True)
        assert adapter.get_name() == "flux"
        assert asyncio.run(adapter.check_health()) is True
    
    def test_replicate_sdxl_adapter_initialization(self):
        """Replicate SDXL adapter initializes correctly."""
        adapter = ReplicateSDXLAdapter(dry_run=True)
        assert adapter.get_name() == "replicate_sdxl"
        assert asyncio.run(adapter.check_health()) is True
    
    def test_figma_adapter_initialization_without_token(self):
        """Figma adapter initializes but unhealthy without token."""
        adapter = FigmaAPIAdapter(api_token=None, dry_run=True)
        assert adapter.get_name() == "figma_api"
        assert asyncio.run(adapter.check_health()) is False
    
    def test_figma_adapter_initialization_with_token(self):
        """Figma adapter healthy with token."""
        adapter = FigmaAPIAdapter(api_token="test_token", dry_run=True)
        assert adapter.get_name() == "figma_api"
        assert asyncio.run(adapter.check_health()) is True
    
    def test_canva_adapter_initialization(self):
        """Canva adapter initializes but unhealthy (not yet implemented)."""
        adapter = CanvaAPIAdapter(dry_run=True)
        assert adapter.get_name() == "canva_api"
        # Canva is not yet implemented, so always unhealthy
        assert asyncio.run(adapter.check_health()) is False
    
    def test_noop_adapter_initialization(self):
        """No-op adapter always healthy."""
        adapter = NoOpMediaAdapter()
        assert adapter.get_name() == "noop_media"
        assert asyncio.run(adapter.check_health()) is True


# ============================================================================
# Test 2: Dry-Run Image Generation
# ============================================================================

class TestDryRunImageGeneration:
    """Test all providers return stub data in dry-run mode."""
    
    @pytest.mark.asyncio
    async def test_sdxl_dry_run_generation(self):
        """SDXL generates stub image in dry-run."""
        adapter = SDXLAdapter(dry_run=True)
        image = await adapter.generate_image("test prompt", width=512, height=512)
        
        assert image is not None
        assert image.provider_name == "sdxl"
        assert image.format == "png"
        assert image.width == 512
        assert image.height == 512
        assert image.content_type == "binary"
        assert image.content == b"SDXL_STUB_IMAGE_DATA"
    
    @pytest.mark.asyncio
    async def test_openai_dry_run_generation(self):
        """OpenAI generates stub image in dry-run."""
        adapter = OpenAIImagesAdapter(dry_run=True)
        image = await adapter.generate_image("test prompt", width=1024, height=1024)
        
        assert image is not None
        assert image.provider_name == "openai_images"
        assert image.format == "png"
        assert image.width == 1024
        assert image.height == 1024
        assert image.content_type == "url"
        assert isinstance(image.content, str)
    
    @pytest.mark.asyncio
    async def test_flux_dry_run_generation(self):
        """Flux generates stub image in dry-run."""
        adapter = FluxAdapter(dry_run=True)
        image = await adapter.generate_image("test prompt")
        
        assert image is not None
        assert image.provider_name == "flux"
        assert image.format == "png"
    
    @pytest.mark.asyncio
    async def test_replicate_dry_run_generation(self):
        """Replicate SDXL generates stub image in dry-run."""
        adapter = ReplicateSDXLAdapter(dry_run=True)
        image = await adapter.generate_image("test prompt")
        
        assert image is not None
        assert image.provider_name == "replicate_sdxl"
        assert image.format == "png"
        assert image.content_type == "url"
    
    @pytest.mark.asyncio
    async def test_noop_dry_run_generation(self):
        """No-op always returns stub image."""
        adapter = NoOpMediaAdapter()
        image = await adapter.generate_image("test prompt")
        
        assert image is not None
        assert image.provider_name == "noop_media"
        assert image.content == b"NOOP_STUB_IMAGE_DATA"
    
    @pytest.mark.asyncio
    async def test_canva_returns_none(self):
        """Canva stub returns None (not implemented)."""
        adapter = CanvaAPIAdapter(dry_run=True)
        image = await adapter.generate_image("test prompt")
        
        assert image is None


# ============================================================================
# Test 3: Chain Provider Ordering & Fallback
# ============================================================================

class TestProviderChainOrdering:
    """Test chain falls back to next provider on failure."""
    
    def test_chain_initialization(self):
        """Chain initializes with correct provider order."""
        providers = [
            SDXLAdapter(dry_run=True),
            OpenAIImagesAdapter(dry_run=True),
            NoOpMediaAdapter(),
        ]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        assert len(chain.providers) == 3
        assert chain.providers[0].get_name() == "sdxl"
        assert chain.providers[1].get_name() == "openai_images"
        assert chain.providers[2].get_name() == "noop_media"
    
    @pytest.mark.asyncio
    async def test_chain_uses_first_healthy_provider(self):
        """Chain returns result from first healthy provider."""
        providers = [
            SDXLAdapter(dry_run=True),
            OpenAIImagesAdapter(dry_run=True),
            NoOpMediaAdapter(),
        ]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        result = await chain.execute_generate_image("test")
        
        assert result is not None
        assert result.provider_name == "sdxl"
    
    @pytest.mark.asyncio
    async def test_chain_fallback_on_provider_unavailable(self):
        """Chain falls back when provider unavailable."""
        providers = [
            CanvaAPIAdapter(dry_run=True),  # Returns None
            NoOpMediaAdapter(),  # Falls back here
        ]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        result = await chain.execute_generate_image("test")
        
        assert result is not None
        assert result.provider_name == "noop_media"
    
    @pytest.mark.asyncio
    async def test_chain_all_providers_fail(self):
        """Chain returns None when all providers fail."""
        # Create a failing provider
        class FailingProvider(MediaGeneratorProvider):
            def get_name(self) -> str:
                return "failing"
            
            async def check_health(self) -> bool:
                return True
            
            async def generate_image(self, prompt: str, width: int = 1024, 
                                    height: int = 1024, **kwargs) -> Optional[GeneratedImage]:
                raise Exception("Intentional failure")
        
        providers = [FailingProvider()]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        result = await chain.execute_generate_image("test")
        
        assert result is None


# ============================================================================
# Test 4: Figma Export (Dry-Run)
# ============================================================================

class TestFigmaExport:
    """Test Figma export functionality."""
    
    @pytest.mark.asyncio
    async def test_figma_export_dry_run(self):
        """Figma export returns stub result in dry-run."""
        adapter = FigmaAPIAdapter(api_token="test_token", dry_run=True)
        
        image = GeneratedImage(
            content=b"test_image_data",
            content_type="binary",
            format="png",
            width=1024,
            height=1024,
            metadata={"test": "data"},
            provider_name="test_provider",
        )
        
        result = await adapter.export_to_figma(
            image=image,
            file_key="test_file_key",
            page_id="test_page_id",
        )
        
        assert result is not None
        assert result.figma_file_key == "test_file_key"
        assert result.page_id == "test_page_id"
        assert "node_" in result.figma_node_id
        assert "figma.com/file" in result.figma_url
    
    @pytest.mark.asyncio
    async def test_figma_export_without_token(self):
        """Figma export fails without token."""
        adapter = FigmaAPIAdapter(api_token=None, dry_run=True)
        
        image = GeneratedImage(
            content=b"test",
            content_type="binary",
            format="png",
            width=1024,
            height=1024,
            metadata={},
            provider_name="test",
        )
        
        result = await adapter.export_to_figma(
            image=image,
            file_key="test_file_key",
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_chain_figma_export(self):
        """Chain executes Figma export with fallback."""
        providers = [
            FigmaAPIAdapter(api_token="test_token", dry_run=True),
            NoOpMediaAdapter(),
        ]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        image = GeneratedImage(
            content=b"test",
            content_type="binary",
            format="png",
            width=1024,
            height=1024,
            metadata={},
            provider_name="test",
        )
        
        result = await chain.execute_export_figma(
            image=image,
            file_key="test_key",
        )
        
        assert result is not None
        assert result.figma_file_key == "test_key"


# ============================================================================
# Test 5: MediaEngine Integration
# ============================================================================

class TestMediaEngineIntegration:
    """Test MediaEngine integration with generation and export."""
    
    def setup_method(self):
        """Reset engine before each test."""
        reset_media_engine()
    
    @pytest.mark.asyncio
    async def test_generate_asset_from_prompt(self):
        """MediaEngine.generate_asset_from_prompt() creates asset."""
        engine = get_media_engine()
        
        asset = await engine.generate_asset_from_prompt(
            prompt="A beautiful sunset",
            width=1024,
            height=1024,
        )
        
        assert asset is not None
        assert isinstance(asset, MediaAsset)
        assert asset.asset_id is not None
        assert "sunset" in asset.description
        
        # Verify asset in library
        assert any(asset.asset_id in lib.assets for lib in engine.libraries.values())
    
    @pytest.mark.asyncio
    async def test_generate_asset_creates_default_library(self):
        """generate_asset_from_prompt creates default library if needed."""
        engine = get_media_engine()
        
        # Verify no libraries exist
        assert len(engine.libraries) == 0
        
        asset = await engine.generate_asset_from_prompt(
            prompt="Test",
        )
        
        # Default library should be created
        assert len(engine.libraries) > 0
    
    @pytest.mark.asyncio
    async def test_generate_asset_adds_to_specified_library(self):
        """generate_asset_from_prompt adds to specified library."""
        engine = get_media_engine()
        
        # Create library
        lib = engine.create_library("Test Library")
        
        asset = await engine.generate_asset_from_prompt(
            prompt="Test",
            library_id=lib.library_id,
        )
        
        assert asset is not None
        assert asset.asset_id in lib.assets
    
    @pytest.mark.asyncio
    async def test_export_asset_to_figma(self):
        """MediaEngine.export_asset_to_figma() exports asset."""
        # Mock the factory to provide a Figma token
        from unittest.mock import patch, MagicMock
        
        engine = get_media_engine()
        
        # Create asset first
        asset = await engine.generate_asset_from_prompt(
            prompt="Test image",
        )
        
        assert asset is not None
        
        # Create a mock Figma provider with token
        mock_figma = FigmaAPIAdapter(api_token="test_token", dry_run=True)
        
        # Patch the factory to return a chain with the mocked Figma provider
        with patch('aicmo.gateways.factory.get_media_generator_chain') as mock_factory:
            from aicmo.media.generators.provider_chain import MediaGeneratorChain
            from aicmo.media.adapters import NoOpMediaAdapter
            
            # Create chain with mocked Figma provider
            chain = MediaGeneratorChain(
                providers=[mock_figma, NoOpMediaAdapter()],
                dry_run=True,
            )
            mock_factory.return_value = chain
            
            # Export to Figma
            result = await engine.export_asset_to_figma(
                asset_id=asset.asset_id,
                file_key="test_file_key",
                page_id="test_page",
            )
        
        assert result is not None
        assert "figma_node_id" in result
        assert "figma_url" in result
        assert result["figma_file_key"] == "test_file_key"
    
    @pytest.mark.asyncio
    async def test_export_nonexistent_asset(self):
        """Exporting nonexistent asset returns None."""
        engine = get_media_engine()
        
        result = await engine.export_asset_to_figma(
            asset_id="nonexistent",
            file_key="test_key",
        )
        
        assert result is None


# ============================================================================
# Test 6: Missing Configuration Handling
# ============================================================================

class TestMissingConfiguration:
    """Test providers handle missing configuration gracefully."""
    
    def test_figma_provider_unhealthy_without_token(self):
        """Figma provider reports unhealthy without token."""
        adapter = FigmaAPIAdapter(api_token=None, dry_run=True)
        health = asyncio.run(adapter.check_health())
        assert health is False
    
    def test_factory_chain_handles_missing_token(self):
        """Factory creates chain even with missing Figma token."""
        # This should not crash
        chain = get_media_generator_chain()
        assert chain is not None
        assert len(chain.providers) > 0


# ============================================================================
# Test 7: Provider Health Tracking
# ============================================================================

class TestProviderHealthTracking:
    """Test chain tracks provider health status."""
    
    @pytest.mark.asyncio
    async def test_chain_tracks_health(self):
        """Chain tracks health of all providers."""
        providers = [
            SDXLAdapter(dry_run=True),
            OpenAIImagesAdapter(dry_run=True),
        ]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        # Generate image (first provider should succeed)
        result = await chain.execute_generate_image("test")
        
        assert result is not None
        
        # Check health tracking
        health = chain.get_provider_health()
        assert "sdxl" in health
        assert health["sdxl"] is True  # First provider succeeded


# ============================================================================
# Test 8: Dynamic Dispatch Verification
# ============================================================================

class TestDynamicDispatch:
    """Verify dynamic dispatch (no hard-coded routing)."""
    
    @pytest.mark.asyncio
    async def test_chain_uses_getattr_dispatch(self):
        """Chain uses getattr for method dispatch (not if/elif)."""
        # Create custom provider
        class CustomProvider(MediaGeneratorProvider):
            def get_name(self) -> str:
                return "custom"
            
            async def check_health(self) -> bool:
                return True
            
            async def generate_image(self, prompt: str, width: int = 1024,
                                   height: int = 1024, **kwargs) -> Optional[GeneratedImage]:
                return GeneratedImage(
                    content=b"CUSTOM_DATA",
                    content_type="binary",
                    format="png",
                    width=width,
                    height=height,
                    metadata={"custom": True},
                    provider_name="custom",
                )
        
        providers = [CustomProvider()]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        # Chain should work with any provider implementing the interface
        result = await chain.execute_generate_image("test")
        
        assert result is not None
        assert result.provider_name == "custom"
        assert result.metadata["custom"] is True


# ============================================================================
# Test 9: Multi-Provider Failover Simulation
# ============================================================================

class TestMultiProviderFailover:
    """Test complex failover scenarios."""
    
    @pytest.mark.asyncio
    async def test_failover_with_mixed_providers(self):
        """Chain correctly fails over with mixed provider states."""
        providers = [
            CanvaAPIAdapter(dry_run=True),  # Not implemented (returns None)
            FluxAdapter(dry_run=True),      # Should succeed here
            NoOpMediaAdapter(),              # Fallback
        ]
        chain = MediaGeneratorChain(providers=providers, dry_run=True)
        
        result = await chain.execute_generate_image("test")
        
        # Should use Flux (second provider)
        assert result is not None
        assert result.provider_name == "flux"


# ============================================================================
# Test 10: Image Metadata Preservation
# ============================================================================

class TestImageMetadataPreservation:
    """Test metadata is preserved through generation and export."""
    
    @pytest.mark.asyncio
    async def test_generated_image_has_metadata(self):
        """Generated images include provider metadata."""
        adapter = SDXLAdapter(dry_run=True)
        image = await adapter.generate_image(
            "test prompt",
            steps=50,
        )
        
        assert image is not None
        assert "provider" in image.metadata
        assert "prompt" in image.metadata
        assert image.metadata["prompt"] == "test prompt"
        assert image.metadata["steps"] == 50


# ============================================================================
# Test 11: Async Compatibility
# ============================================================================

class TestAsyncCompatibility:
    """Test async/await patterns work correctly."""
    
    @pytest.mark.asyncio
    async def test_async_generation_pipeline(self):
        """Full async pipeline works correctly."""
        engine = get_media_engine()
        
        # Generate multiple assets concurrently
        tasks = [
            engine.generate_asset_from_prompt(f"Prompt {i}")
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(r is not None for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
