"""
Phase 4.7: Figma Template Engine Tests

Tests for automatic template application with generated assets.
"""

import pytest
from aicmo.media.figma_templates import (
    FigmaTemplateConfig,
    FigmaTemplateEngine,
    CarouselSlide,
    FigmaTemplateApplication,
)
from aicmo.media.engine import MediaEngine, get_media_engine, reset_media_engine
from aicmo.media.models import MediaAsset, MediaType, MediaDimensions


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


@pytest.fixture
def figma_engine():
    """Create Figma template engine."""
    return FigmaTemplateEngine()


@pytest.fixture
def simple_template():
    """Create simple carousel template."""
    return FigmaTemplateConfig(
        file_key="test_file_key_123",
        name="Simple Carousel",
        description="Simple 3-slide carousel",
        template_type="carousel",
        frame_mapping={
            "slide_1_image": "node_slide1_image",
            "slide_2_image": "node_slide2_image",
            "slide_3_image": "node_slide3_image",
        },
        text_nodes={
            "slide_1_title": "node_slide1_title",
            "slide_2_title": "node_slide2_title",
            "slide_3_title": "node_slide3_title",
            "slide_1_description": "node_slide1_desc",
        },
    )


class TestFigmaTemplateConfig:
    """Test FigmaTemplateConfig initialization."""
    
    def test_create_basic_template(self):
        """Should create basic template config."""
        config = FigmaTemplateConfig(
            file_key="file_123",
            name="Test Template",
        )
        
        assert config.file_key == "file_123"
        assert config.name == "Test Template"
        assert config.frame_mapping == {}
        assert config.text_nodes == {}
    
    def test_create_template_with_mappings(self):
        """Should create template with slot mappings."""
        config = FigmaTemplateConfig(
            file_key="file_123",
            frame_mapping={"main": "node_main"},
            text_nodes={"title": "node_title"},
        )
        
        assert "main" in config.frame_mapping
        assert "title" in config.text_nodes
    
    def test_template_with_page_id(self):
        """Should support Figma page ID."""
        config = FigmaTemplateConfig(
            file_key="file_123",
            page_id="page_456",
        )
        
        assert config.page_id == "page_456"


class TestCarouselSlide:
    """Test CarouselSlide definition."""
    
    def test_create_carousel_slide(self):
        """Should create carousel slide."""
        slide = CarouselSlide(
            slide_id="slide_1",
            image_slot="main_image",
            text_slots=["title", "description"],
            order=1,
        )
        
        assert slide.slide_id == "slide_1"
        assert slide.image_slot == "main_image"
        assert len(slide.text_slots) == 2


class TestFigmaTemplateEngine:
    """Test Figma template engine."""
    
    def test_engine_initialization(self, figma_engine):
        """Should initialize template engine."""
        assert figma_engine.media_engine is None
        assert len(figma_engine.applications) == 0
    
    def test_engine_with_media_engine(self, engine, figma_engine):
        """Should accept media engine reference."""
        figma_engine.media_engine = engine
        assert figma_engine.media_engine is not None
    
    def test_apply_carousel_basic(self, figma_engine, simple_template):
        """Should apply carousel template."""
        assets = {
            "slide_1_image": "asset_1",
            "slide_2_image": "asset_2",
        }
        texts = {
            "slide_1_title": "First Slide",
            "slide_2_title": "Second Slide",
        }
        
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets=assets,
            texts=texts,
        )
        
        assert isinstance(result, FigmaTemplateApplication)
        assert result.status == "applied"
        assert result.file_key == "test_file_key_123"
    
    def test_apply_carousel_with_export(self, figma_engine, simple_template):
        """Should export template when requested."""
        assets = {"slide_1_image": "asset_1"}
        texts = {"slide_1_title": "Title"}
        
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets=assets,
            texts=texts,
            export=True,
        )
        
        assert result.status == "exported"
        assert result.export_url is not None
        assert "figma.com" in result.export_url
    
    def test_apply_carousel_missing_file_key(self, figma_engine):
        """Should handle missing file_key gracefully."""
        template = FigmaTemplateConfig(file_key="")
        
        result = figma_engine.apply_carousel_template(
            template=template,
            assets={},
            texts={},
        )
        
        assert result.status == "failed"
    
    def test_apply_carousel_maps_slots(self, figma_engine, simple_template):
        """Should correctly map slot names to node IDs."""
        assets = {"slide_1_image": "asset_1"}
        texts = {"slide_1_title": "Title"}
        
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets=assets,
            texts=texts,
        )
        
        # Should have node mappings
        assert len(result.node_ids) > 0
    
    def test_apply_carousel_unknown_slot_warning(self, figma_engine, simple_template):
        """Should warn about unknown slot names."""
        assets = {
            "unknown_slot": "asset_1",
            "slide_1_image": "asset_2",
        }
        texts = {
            "unknown_text": "content",
        }
        
        # Should not crash, but log warnings
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets=assets,
            texts=texts,
        )
        
        assert isinstance(result, FigmaTemplateApplication)
    
    def test_apply_single_image_template(self, figma_engine, simple_template):
        """Should apply single image template."""
        result = figma_engine.apply_single_image_template(
            template=simple_template,
            asset="asset_123",
            metadata={"title": "My Image", "description": "Beautiful"},
        )
        
        assert isinstance(result, FigmaTemplateApplication)
    
    def test_apply_multi_panel_template(self, figma_engine, simple_template):
        """Should apply multi-panel template."""
        panels = [
            {"image": "asset_1", "title": "Panel 1", "description": "First"},
            {"image": "asset_2", "title": "Panel 2", "description": "Second"},
        ]
        
        result = figma_engine.apply_multi_panel_template(
            template=simple_template,
            panels=panels,
        )
        
        assert isinstance(result, FigmaTemplateApplication)
    
    def test_get_application(self, figma_engine, simple_template):
        """Should retrieve stored application by ID."""
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets={},
            texts={},
        )
        
        retrieved = figma_engine.get_application(result.application_id)
        assert retrieved is not None
        assert retrieved.application_id == result.application_id
    
    def test_get_application_not_found(self, figma_engine):
        """Should return None for unknown application ID."""
        result = figma_engine.get_application("unknown_id")
        assert result is None
    
    def test_list_applications(self, figma_engine, simple_template):
        """Should list all applications."""
        figma_engine.apply_carousel_template(
            template=simple_template,
            assets={},
            texts={},
        )
        figma_engine.apply_carousel_template(
            template=simple_template,
            assets={},
            texts={},
        )
        
        apps = figma_engine.list_applications()
        assert len(apps) == 2
    
    def test_export_application(self, figma_engine, simple_template):
        """Should export application to Figma."""
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets={},
            texts={},
        )
        
        export_url = figma_engine.export_application(result.application_id)
        assert export_url is not None
        assert "figma.com" in export_url


class TestMediaEngineCarouselIntegration:
    """Test integration of carousel templates with MediaEngine."""
    
    def test_apply_carousel_to_figma_basic(self, engine):
        """Should apply carousel template from MediaEngine."""
        # Create library and asset
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test Image",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        # Create template
        template = FigmaTemplateConfig(
            file_key="file_123",
            frame_mapping={"main": "node_main"},
            text_nodes={"title": "node_title"},
        )
        
        # Apply template
        result = engine.apply_carousel_to_figma(
            template_config=template,
            asset_ids_by_slot={"main": asset.asset_id},
            texts_by_slot={"title": "My Title"},
        )
        
        assert result is not None
        assert "template_application_id" in result
    
    def test_apply_carousel_with_missing_asset(self, engine):
        """Should handle missing asset gracefully."""
        template = FigmaTemplateConfig(
            file_key="file_123",
            frame_mapping={"main": "node_main"},
        )
        
        # Reference non-existent asset
        result = engine.apply_carousel_to_figma(
            template_config=template,
            asset_ids_by_slot={"main": "non_existent_id"},
            texts_by_slot={},
        )
        
        # Should still return result (with warnings logged)
        assert result is not None
    
    def test_apply_carousel_export_url(self, engine):
        """Should return export URL in result."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        template = FigmaTemplateConfig(
            file_key="file_123",
            frame_mapping={"main": "node_main"},
        )
        
        result = engine.apply_carousel_to_figma(
            template_config=template,
            asset_ids_by_slot={"main": asset.asset_id},
            texts_by_slot={},
        )
        
        if result:
            assert "export_url" in result


class TestTemplateEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_assets_and_texts(self, figma_engine, simple_template):
        """Should handle empty assets and texts."""
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets={},
            texts={},
        )
        
        assert result.status == "applied"
    
    def test_large_number_of_slots(self, figma_engine):
        """Should handle template with many slots."""
        template = FigmaTemplateConfig(
            file_key="file_123",
            frame_mapping={f"slot_{i}": f"node_{i}" for i in range(100)},
            text_nodes={f"text_{i}": f"text_node_{i}" for i in range(100)},
        )
        
        result = figma_engine.apply_carousel_template(
            template=template,
            assets={},
            texts={},
        )
        
        assert isinstance(result, FigmaTemplateApplication)
    
    def test_special_characters_in_content(self, figma_engine, simple_template):
        """Should handle special characters in text."""
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets={"slide_1_image": "asset_1"},
            texts={"slide_1_title": "Title with émojis 🎨 & special chars!"},
        )
        
        assert isinstance(result, FigmaTemplateApplication)
    
    def test_very_long_text_content(self, figma_engine, simple_template):
        """Should handle very long text."""
        long_text = "A" * 10000
        
        result = figma_engine.apply_carousel_template(
            template=simple_template,
            assets={},
            texts={"slide_1_title": long_text},
        )
        
        assert isinstance(result, FigmaTemplateApplication)
