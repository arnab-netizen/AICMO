"""Tests for Advanced Creative Production Engine.

Stage C: Creative engine tests
"""

import pytest
from datetime import datetime
from unittest.mock import patch
import tempfile
import os

from aicmo.domain.intake import ClientIntake
from aicmo.creatives.domain import (
    CreativeType,
    VideoStyle,
    AspectRatio,
    VideoSpec,
    MotionGraphicsSpec,
    MoodboardItem,
    Moodboard,
    Storyboard,
    CreativeAsset,
    CreativeProject,
)
from aicmo.creatives.service import (
    generate_video_storyboard,
    generate_moodboard,
    generate_motion_graphics_spec,
    create_creative_project,
)
from aicmo.learning.event_types import EventType


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_intake():
    """Sample client intake for testing."""
    return ClientIntake(
        brand_name="CreativeTestCo",
        industry="Technology",
        product_service="SaaS Platform",
        primary_goal="Build brand awareness",
        target_audiences=["Tech professionals", "Startups"],
        timeline="90 days"
    )


# ═══════════════════════════════════════════════════════════════════════
# Domain Model Tests
# ═══════════════════════════════════════════════════════════════════════


class TestVideoSpecDomain:
    """Test VideoSpec domain model."""
    
    def test_video_spec_creation(self):
        """Test creating a video spec."""
        spec = VideoSpec(
            duration_seconds=30,
            aspect_ratio=AspectRatio.HORIZONTAL,
            style=VideoStyle.MOTION_GRAPHICS,
            scenes=["Scene 1", "Scene 2"],
            voiceover_script="Test script",
            target_platform="YouTube"
        )
        
        assert spec.duration_seconds == 30
        assert spec.aspect_ratio == AspectRatio.HORIZONTAL
        assert spec.style == VideoStyle.MOTION_GRAPHICS
        assert len(spec.scenes) == 2
    
    def test_video_spec_defaults(self):
        """Test video spec default values."""
        spec = VideoSpec(
            duration_seconds=15,
            aspect_ratio=AspectRatio.SQUARE,
            style=VideoStyle.LIVE_ACTION
        )
        
        assert spec.fps == 30
        assert spec.resolution == "1080p"
        assert len(spec.scenes) == 0


class TestMoodboardDomain:
    """Test Moodboard domain model."""
    
    def test_moodboard_creation(self):
        """Test creating a moodboard."""
        items = [
            MoodboardItem(
                image_description="Color palette",
                category="color"
            ),
            MoodboardItem(
                image_description="Typography",
                category="typography"
            )
        ]
        
        moodboard = Moodboard(
            title="Test Moodboard",
            brand_name="TestBrand",
            purpose="Brand identity",
            items=items,
            overall_aesthetic="modern",
            color_palette=["#FF0000", "#00FF00"],
            keywords=["tech", "modern"],
            created_at=datetime.now()
        )
        
        assert moodboard.title == "Test Moodboard"
        assert len(moodboard.items) == 2
        assert len(moodboard.color_palette) == 2


class TestStoryboardDomain:
    """Test Storyboard domain model."""
    
    def test_storyboard_creation(self):
        """Test creating a storyboard."""
        scenes = [
            {"scene_number": 1, "duration_seconds": 10},
            {"scene_number": 2, "duration_seconds": 10}
        ]
        
        storyboard = Storyboard(
            title="Test Storyboard",
            brand_name="TestBrand",
            video_purpose="Product demo",
            total_duration_seconds=20,
            aspect_ratio=AspectRatio.HORIZONTAL,
            scenes=scenes,
            created_at=datetime.now()
        )
        
        assert storyboard.title == "Test Storyboard"
        assert storyboard.total_duration_seconds == 20
        assert len(storyboard.scenes) == 2


# ═══════════════════════════════════════════════════════════════════════
# Service Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestVideoStoryboardGeneration:
    """Test video storyboard generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_storyboard_returns_storyboard(self, temp_db, sample_intake):
        """Test that generate_video_storyboard returns a storyboard."""
        storyboard = generate_video_storyboard(
            sample_intake,
            video_purpose="Product demo",
            duration_seconds=30
        )
        
        assert isinstance(storyboard, Storyboard)
        assert storyboard.brand_name == sample_intake.brand_name
        assert storyboard.total_duration_seconds == 30
    
    def test_storyboard_has_scenes(self, temp_db, sample_intake):
        """Test that generated storyboard includes scenes."""
        storyboard = generate_video_storyboard(
            sample_intake,
            video_purpose="Brand story",
            duration_seconds=45
        )
        
        assert len(storyboard.scenes) > 0
        # Should have 3-act structure
        assert len(storyboard.scenes) >= 3
    
    def test_storyboard_logs_event(self, temp_db, sample_intake):
        """Test that storyboard generation logs learning event."""
        with patch('aicmo.creatives.service.log_event') as mock_log:
            generate_video_storyboard(sample_intake, video_purpose="Test")
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ADV_CREATIVE_STORYBOARD_GENERATED.value


class TestMoodboardGeneration:
    """Test moodboard generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_moodboard_returns_moodboard(self, temp_db, sample_intake):
        """Test that generate_moodboard returns a moodboard."""
        moodboard = generate_moodboard(
            sample_intake,
            purpose="Brand identity",
            aesthetic="modern"
        )
        
        assert isinstance(moodboard, Moodboard)
        assert moodboard.brand_name == sample_intake.brand_name
        assert moodboard.overall_aesthetic == "modern"
    
    def test_moodboard_has_items(self, temp_db, sample_intake):
        """Test that generated moodboard includes items."""
        moodboard = generate_moodboard(sample_intake)
        
        assert len(moodboard.items) > 0
        assert len(moodboard.color_palette) > 0
        assert len(moodboard.keywords) > 0
    
    def test_moodboard_logs_event(self, temp_db, sample_intake):
        """Test that moodboard generation logs learning event."""
        with patch('aicmo.creatives.service.log_event') as mock_log:
            generate_moodboard(sample_intake, purpose="Campaign")
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ADV_CREATIVE_MOODBOARD_GENERATED.value


class TestMotionGraphicsGeneration:
    """Test motion graphics spec generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_motion_spec_returns_spec(self, temp_db, sample_intake):
        """Test that generate_motion_graphics_spec returns a spec."""
        messages = ["Launch your product", "Grow your business", "Scale faster"]
        spec = generate_motion_graphics_spec(
            sample_intake,
            key_messages=messages,
            duration_seconds=15
        )
        
        assert isinstance(spec, MotionGraphicsSpec)
        assert spec.duration_seconds == 15
        assert len(spec.key_messages) == 3
    
    def test_motion_spec_has_style_params(self, temp_db, sample_intake):
        """Test that motion spec includes style parameters."""
        spec = generate_motion_graphics_spec(
            sample_intake,
            key_messages=["Message 1"],
            aspect_ratio=AspectRatio.SQUARE
        )
        
        assert spec.aspect_ratio == AspectRatio.SQUARE
        assert len(spec.color_palette) > 0
        assert spec.animation_style in ["smooth", "energetic", "minimal"]
    
    def test_motion_spec_logs_event(self, temp_db, sample_intake):
        """Test that motion graphics spec logs learning event."""
        with patch('aicmo.creatives.service.log_event') as mock_log:
            generate_motion_graphics_spec(sample_intake, key_messages=["Test"])
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ADV_CREATIVE_MOTION_GENERATED.value


class TestCreativeProjectManagement:
    """Test creative project management."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_create_project_returns_project(self, temp_db, sample_intake):
        """Test that create_creative_project returns a project."""
        deliverables = ["Video", "Motion graphics", "Moodboard"]
        project = create_creative_project(
            sample_intake,
            project_name="Q1 Campaign",
            deliverables=deliverables
        )
        
        assert isinstance(project, CreativeProject)
        assert project.brand_name == sample_intake.brand_name
        assert len(project.deliverables) == 3
    
    def test_project_has_metadata(self, temp_db, sample_intake):
        """Test that project includes proper metadata."""
        project = create_creative_project(
            sample_intake,
            project_name="Test Project",
            deliverables=["Video"]
        )
        
        assert project.project_id  # Should have UUID
        assert project.status == "planning"
        assert project.created_at
    
    def test_project_creation_logs_event(self, temp_db, sample_intake):
        """Test that project creation logs learning event."""
        with patch('aicmo.creatives.service.log_event') as mock_log:
            create_creative_project(
                sample_intake,
                project_name="Test",
                deliverables=["Video"]
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ADV_CREATIVE_STORYBOARD_GENERATED.value  # Placeholder


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestCreativeEngineIntegration:
    """Test creative engine integration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_creative_workflow_end_to_end(self, temp_db):
        """Test complete creative production workflow."""
        # Create intake
        intake = ClientIntake(
            brand_name="WorkflowTest",
            industry="FinTech",
            product_service="Payment platform",
            primary_goal="Product launch",
            target_audiences=["SMB owners"]
        )
        
        # Generate moodboard
        moodboard = generate_moodboard(intake, purpose="Campaign", aesthetic="professional")
        assert len(moodboard.items) > 0
        
        # Generate storyboard
        storyboard = generate_video_storyboard(intake, video_purpose="Launch video", duration_seconds=30)
        assert len(storyboard.scenes) >= 3
        
        # Generate motion graphics spec
        motion_spec = generate_motion_graphics_spec(
            intake,
            key_messages=["Fast", "Secure", "Simple"]
        )
        assert len(motion_spec.key_messages) == 3
        
        # Create project
        project = create_creative_project(
            intake,
            project_name="Launch Campaign",
            deliverables=["Video", "Motion graphics", "Moodboard"]
        )
        assert project.status == "planning"
        
        # Note: Learning events are tested separately in other test methods
