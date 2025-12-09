"""
Tests for Brand Strategy Engine (Stage B).

Validates brand architecture, positioning, narrative generation with learning hooks.
"""

import pytest
import tempfile
import os
from unittest.mock import patch

from aicmo.brand.domain import (
    BrandCore,
    BrandPositioning,
    BrandArchitecture,
    BrandNarrative,
    BrandStrategy,
)
from aicmo.brand.service import (
    generate_brand_core,
    generate_brand_positioning,
    generate_brand_architecture,
    generate_brand_narrative,
    generate_complete_brand_strategy,
)
from aicmo.domain.intake import ClientIntake
from aicmo.learning.event_types import EventType


class TestBrandCoreDomain:
    """Test BrandCore domain model."""
    
    def test_brand_core_minimal(self):
        """BrandCore can be created with required fields."""
        core = BrandCore(
            purpose="To help businesses grow",
            vision="Leading platform",
            mission="Deliver results",
            values=["Excellence", "Innovation"]
        )
        
        assert core.purpose == "To help businesses grow"
        assert len(core.values) == 2
    
    def test_brand_core_with_personality(self):
        """BrandCore can include personality and voice."""
        core = BrandCore(
            purpose="Transform industry",
            vision="Be the best",
            mission="Help clients succeed",
            values=["Trust", "Quality"],
            personality_traits=["Bold", "Innovative"],
            voice_characteristics=["Clear", "Confident"]
        )
        
        assert len(core.personality_traits) == 2
        assert len(core.voice_characteristics) == 2


class TestBrandPositioningDomain:
    """Test BrandPositioning domain model."""
    
    def test_positioning_framework(self):
        """BrandPositioning follows classical framework."""
        positioning = BrandPositioning(
            target_audience="Tech startups",
            frame_of_reference="Marketing platforms",
            point_of_difference="AI-powered automation",
            reason_to_believe="Proven results"
        )
        
        assert positioning.target_audience == "Tech startups"
        assert positioning.point_of_difference == "AI-powered automation"
    
    def test_positioning_extended(self):
        """BrandPositioning can include extended attributes."""
        positioning = BrandPositioning(
            target_audience="Enterprise",
            frame_of_reference="SaaS",
            point_of_difference="Unique approach",
            reason_to_believe="Track record",
            competitive_alternatives=["Competitor A", "Competitor B"],
            key_benefits=["Speed", "Quality"]
        )
        
        assert len(positioning.competitive_alternatives) == 2
        assert len(positioning.key_benefits) == 2


class TestBrandArchitectureDomain:
    """Test BrandArchitecture domain model."""
    
    def test_architecture_basic(self):
        """BrandArchitecture with core structure."""
        architecture = BrandArchitecture(
            core_brand_name="TestBrand",
            core_brand_description="Leading platform",
            pillars=["Pillar 1", "Pillar 2", "Pillar 3"]
        )
        
        assert architecture.core_brand_name == "TestBrand"
        assert len(architecture.pillars) == 3
        assert architecture.architecture_type == "branded_house"
    
    def test_architecture_with_sub_brands(self):
        """BrandArchitecture can include sub-brands."""
        architecture = BrandArchitecture(
            core_brand_name="MasterBrand",
            core_brand_description="Parent company",
            sub_brands=["Product A", "Product B"],
            pillars=["Innovation", "Quality"],
            architecture_type="house_of_brands"
        )
        
        assert len(architecture.sub_brands) == 2
        assert architecture.architecture_type == "house_of_brands"


class TestBrandNarrativeDomain:
    """Test BrandNarrative domain model."""
    
    def test_narrative_basic(self):
        """BrandNarrative with story and pitch."""
        narrative = BrandNarrative(
            brand_story="Once upon a time...",
            elevator_pitch="We help companies grow"
        )
        
        assert len(narrative.brand_story) > 0
        assert len(narrative.elevator_pitch) > 0
    
    def test_narrative_with_messaging(self):
        """BrandNarrative can include full messaging."""
        narrative = BrandNarrative(
            brand_story="Full story here",
            tagline="Excellence in Action",
            elevator_pitch="30-second pitch",
            key_messages=["Message 1", "Message 2", "Message 3"],
            rtbs=["RTB 1", "RTB 2"]
        )
        
        assert narrative.tagline == "Excellence in Action"
        assert len(narrative.key_messages) == 3
        assert len(narrative.rtbs) == 2


class TestBrandCoreGeneration:
    """Test brand core generation service."""
    
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
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.fixture
    def sample_intake(self):
        """Create sample client intake."""
        return ClientIntake(
            brand_name="TechCorp",
            industry="Technology",
            primary_goal="Increase brand awareness",
            target_audience="Tech professionals",
            timeline="Q1 2026"
        )
    
    def test_generate_brand_core_returns_core(self, temp_db, sample_intake):
        """generate_brand_core returns BrandCore object."""
        core = generate_brand_core(sample_intake)
        
        assert isinstance(core, BrandCore)
        assert core.purpose
        assert core.vision
        assert core.mission
        assert len(core.values) > 0
    
    def test_brand_core_has_all_elements(self, temp_db, sample_intake):
        """Generated brand core has all required elements."""
        core = generate_brand_core(sample_intake)
        
        assert isinstance(core.purpose, str) and len(core.purpose) > 0
        assert isinstance(core.vision, str) and len(core.vision) > 0
        assert isinstance(core.mission, str) and len(core.mission) > 0
        assert isinstance(core.values, list) and len(core.values) >= 3
    
    def test_brand_core_logs_event(self, temp_db, sample_intake):
        """Brand core generation logs learning event."""
        with patch('aicmo.brand.service.log_event') as mock_log:
            generate_brand_core(sample_intake)
            
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == EventType.BRAND_CORE_GENERATED.value


class TestBrandPositioningGeneration:
    """Test brand positioning generation service."""
    
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
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.fixture
    def sample_intake(self):
        """Create sample client intake."""
        return ClientIntake(
            brand_name="SaasCo",
            industry="B2B SaaS",
            primary_goal="Market leadership",
            target_audience="Enterprise buyers",
            timeline="2026"
        )
    
    def test_generate_positioning_returns_positioning(self, temp_db, sample_intake):
        """generate_brand_positioning returns BrandPositioning object."""
        positioning = generate_brand_positioning(sample_intake)
        
        assert isinstance(positioning, BrandPositioning)
        assert positioning.target_audience
        assert positioning.frame_of_reference
        assert positioning.point_of_difference
        assert positioning.reason_to_believe
    
    def test_positioning_follows_framework(self, temp_db, sample_intake):
        """Positioning follows classical positioning framework."""
        positioning = generate_brand_positioning(sample_intake)
        
        # All four framework elements must be present
        assert len(positioning.target_audience) > 0
        assert len(positioning.frame_of_reference) > 0
        assert len(positioning.point_of_difference) > 0
        assert len(positioning.reason_to_believe) > 0
    
    def test_positioning_logs_event(self, temp_db, sample_intake):
        """Positioning generation logs learning event."""
        with patch('aicmo.brand.service.log_event') as mock_log:
            generate_brand_positioning(sample_intake)
            
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == EventType.BRAND_POSITIONING_GENERATED.value


class TestBrandArchitectureGeneration:
    """Test brand architecture generation service."""
    
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
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.fixture
    def sample_intake(self):
        """Create sample client intake."""
        return ClientIntake(
            brand_name="ArchCorp",
            industry="Retail",
            primary_goal="Brand transformation",
            timeline="12 months"
        )
    
    def test_generate_architecture_returns_architecture(self, temp_db, sample_intake):
        """generate_brand_architecture returns BrandArchitecture object."""
        architecture = generate_brand_architecture(sample_intake)
        
        assert isinstance(architecture, BrandArchitecture)
        assert architecture.core_brand_name == sample_intake.brand_name
        assert len(architecture.pillars) > 0
    
    def test_architecture_has_pillars(self, temp_db, sample_intake):
        """Generated architecture includes strategic pillars."""
        architecture = generate_brand_architecture(sample_intake)
        
        assert len(architecture.pillars) >= 3
        assert all(isinstance(p, str) for p in architecture.pillars)
    
    def test_architecture_logs_event(self, temp_db, sample_intake):
        """Architecture generation logs learning event."""
        with patch('aicmo.brand.service.log_event') as mock_log:
            generate_brand_architecture(sample_intake)
            
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == EventType.BRAND_ARCHITECTURE_GENERATED.value


class TestBrandNarrativeGeneration:
    """Test brand narrative generation service."""
    
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
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.fixture
    def sample_architecture(self):
        """Create sample architecture."""
        return BrandArchitecture(
            core_brand_name="NarrativeCo",
            core_brand_description="Leading platform",
            pillars=["Innovation", "Quality", "Service"]
        )
    
    def test_generate_narrative_returns_narrative(self, temp_db, sample_architecture):
        """generate_brand_narrative returns BrandNarrative object."""
        narrative = generate_brand_narrative(sample_architecture)
        
        assert isinstance(narrative, BrandNarrative)
        assert len(narrative.brand_story) > 0
        assert len(narrative.elevator_pitch) > 0
    
    def test_narrative_has_messaging(self, temp_db, sample_architecture):
        """Generated narrative includes key messages."""
        narrative = generate_brand_narrative(sample_architecture)
        
        assert len(narrative.key_messages) > 0
        assert len(narrative.rtbs) > 0
    
    def test_narrative_logs_event(self, temp_db, sample_architecture):
        """Narrative generation logs learning event."""
        with patch('aicmo.brand.service.log_event') as mock_log:
            generate_brand_narrative(sample_architecture)
            
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == EventType.BRAND_NARRATIVE_GENERATED.value
    
    def test_narrative_with_core_and_positioning(self, temp_db, sample_architecture):
        """Narrative can be generated with core and positioning."""
        core = BrandCore(
            purpose="Help businesses",
            vision="Be the best",
            mission="Deliver excellence",
            values=["Trust", "Quality"]
        )
        
        positioning = BrandPositioning(
            target_audience="SMBs",
            frame_of_reference="Platform",
            point_of_difference="AI-powered",
            reason_to_believe="Track record"
        )
        
        narrative = generate_brand_narrative(sample_architecture, core, positioning)
        
        assert isinstance(narrative, BrandNarrative)
        # Story should incorporate positioning elements
        assert positioning.target_audience in narrative.elevator_pitch or \
               positioning.point_of_difference in narrative.elevator_pitch


class TestCompleteBrandStrategy:
    """Test complete brand strategy generation."""
    
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
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.fixture
    def sample_intake(self):
        """Create sample client intake."""
        return ClientIntake(
            brand_name="CompleteCo",
            industry="Healthcare",
            primary_goal="Market transformation",
            target_audience="Healthcare providers",
            timeline="18 months"
        )
    
    def test_generate_complete_strategy(self, temp_db, sample_intake):
        """generate_complete_brand_strategy returns full BrandStrategy."""
        strategy = generate_complete_brand_strategy(sample_intake)
        
        assert isinstance(strategy, BrandStrategy)
        assert strategy.client_name == sample_intake.brand_name
        
        # All components should be present
        assert isinstance(strategy.core, BrandCore)
        assert isinstance(strategy.positioning, BrandPositioning)
        assert isinstance(strategy.architecture, BrandArchitecture)
        assert isinstance(strategy.narrative, BrandNarrative)
    
    def test_complete_strategy_has_summary(self, temp_db, sample_intake):
        """Complete strategy includes executive summary."""
        strategy = generate_complete_brand_strategy(sample_intake)
        
        assert strategy.executive_summary is not None
        assert len(strategy.executive_summary) > 0
    
    def test_complete_strategy_logs_all_events(self, temp_db, sample_intake):
        """Complete strategy generation logs all component events."""
        with patch('aicmo.brand.service.log_event') as mock_log:
            generate_complete_brand_strategy(sample_intake)
            
            # Should log 4 events: core, positioning, architecture, narrative
            assert mock_log.call_count == 4
            
            event_types = [call[0][0] for call in mock_log.call_args_list]
            assert EventType.BRAND_CORE_GENERATED.value in event_types
            assert EventType.BRAND_POSITIONING_GENERATED.value in event_types
            assert EventType.BRAND_ARCHITECTURE_GENERATED.value in event_types
            assert EventType.BRAND_NARRATIVE_GENERATED.value in event_types


class TestBrandEngineIntegration:
    """Integration tests for brand engine."""
    
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
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_brand_strategy_workflow(self, temp_db):
        """Test complete brand strategy workflow."""
        # Create intake
        intake = ClientIntake(
            brand_name="WorkflowTest",
            industry="FinTech",
            primary_goal="Category leadership",
            target_audiences=["Financial institutions"],
            timeline="2 years"
        )
        
        # Generate complete strategy
        strategy = generate_complete_brand_strategy(intake)
        
        # Verify all components are properly integrated
        assert strategy.core.purpose
        assert strategy.positioning.target_audience == intake.target_audiences[0]
        assert strategy.architecture.core_brand_name == intake.brand_name
        assert len(strategy.narrative.brand_story) > 0
        
        # Verify cross-component consistency
        assert intake.brand_name in strategy.narrative.brand_story or \
               intake.brand_name in strategy.narrative.elevator_pitch
