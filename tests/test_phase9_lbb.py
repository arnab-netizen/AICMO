"""
Phase 9 Tests: Living Brand Brain (LBB) Implementation

Tests cover:
1. BrandMemory model (creation, serialization, insights)
2. BrandBrainRepository (persistence, retrieval, cleanup)
3. BrandBrainInsightExtractor (insight extraction from outputs)
4. generate_with_brand_brain wrapper function
5. Integration with existing generators
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from aicmo.brand.memory import (
    BrandMemory,
    BrandGenerationRecord,
    BrandGenerationInsight,
)
from aicmo.brand.repository import BrandBrainRepository
from aicmo.brand.brain import (
    BrandBrainInsightExtractor,
    generate_with_brand_brain,
    get_brand_memory,
    get_brand_insights,
)


class TestBrandGenerationInsight:
    """Test BrandGenerationInsight data model."""
    
    def test_insight_creation(self):
        """Test creating a BrandGenerationInsight."""
        insight = BrandGenerationInsight(
            insight_text="Audience prefers short-form video",
            confidence=0.85,
            frequency=3,
            last_seen=datetime.utcnow(),
            source_context="Social calendar generation",
            generator_type="social_calendar_generator",
        )
        assert insight.insight_text == "Audience prefers short-form video"
        assert insight.confidence == 0.85
        assert insight.frequency == 3
    
    def test_insight_serialization(self):
        """Test serializing and deserializing insights."""
        insight = BrandGenerationInsight(
            insight_text="Test insight",
            confidence=0.7,
            frequency=2,
            last_seen=datetime.utcnow(),
            source_context="test",
            generator_type="test_generator",
        )
        
        serialized = insight.to_dict()
        assert serialized["insight_text"] == "Test insight"
        assert serialized["confidence"] == 0.7
        assert "last_seen" in serialized
        
        deserialized = BrandGenerationInsight.from_dict(serialized)
        assert deserialized.insight_text == insight.insight_text
        assert deserialized.confidence == insight.confidence


class TestBrandGenerationRecord:
    """Test BrandGenerationRecord data model."""
    
    def test_record_creation(self):
        """Test creating a BrandGenerationRecord."""
        record = BrandGenerationRecord(
            generation_id="gen-123",
            generator_type="swot_generator",
            brand_id="brand-1",
            brief_id="brief-1",
            prompt="Generate SWOT analysis",
            brief_summary="Tech startup brief",
            output_json={"strengths": ["Fast", "Innovative"]},
            llm_provider="claude",
            completion_time_ms=1234.5,
        )
        assert record.generation_id == "gen-123"
        assert record.generator_type == "swot_generator"
        assert record.completion_time_ms == 1234.5
    
    def test_record_serialization(self):
        """Test serializing and deserializing generation records."""
        record = BrandGenerationRecord(
            generation_id="gen-456",
            generator_type="persona_generator",
            brand_id="brand-2",
            brief_id=None,
            prompt="Generate personas",
            brief_summary=None,
            output_json={"personas": []},
            llm_provider="openai",
            completion_time_ms=800.0,
            extracted_insights=[
                BrandGenerationInsight(
                    insight_text="Young demographic",
                    confidence=0.9,
                    frequency=1,
                    last_seen=datetime.utcnow(),
                    source_context="Personas",
                    generator_type="persona_generator",
                )
            ],
        )
        
        serialized = record.to_dict()
        assert serialized["generation_id"] == "gen-456"
        assert len(serialized["extracted_insights"]) == 1
        
        deserialized = BrandGenerationRecord.from_dict(serialized)
        assert deserialized.generation_id == record.generation_id
        assert len(deserialized.extracted_insights) == 1


class TestBrandMemory:
    """Test BrandMemory model and consolidation."""
    
    def test_memory_creation(self):
        """Test creating a BrandMemory."""
        memory = BrandMemory(
            brand_id="brand-1",
            brand_name="TechStartup Inc",
        )
        assert memory.brand_id == "brand-1"
        assert memory.brand_name == "TechStartup Inc"
        assert memory.total_generations == 0
    
    def test_add_generation_record(self):
        """Test adding generation records to memory."""
        memory = BrandMemory(
            brand_id="brand-1",
            brand_name="TestBrand",
        )
        
        record = BrandGenerationRecord(
            generation_id="gen-1",
            generator_type="swot_generator",
            brand_id="brand-1",
            brief_id=None,
            prompt="Test",
            brief_summary=None,
            output_json={"test": "data"},
            llm_provider="claude",
            completion_time_ms=500.0,
        )
        
        memory.add_generation_record(record)
        assert memory.total_generations == 1
        assert len(memory.generation_history) == 1
    
    def test_get_insight_summary(self):
        """Test generating insight summary."""
        memory = BrandMemory(
            brand_id="brand-1",
            brand_name="TestBrand",
            consolidated_insights=[
                BrandGenerationInsight(
                    insight_text="Insight 1",
                    confidence=0.9,
                    frequency=5,
                    last_seen=datetime.utcnow(),
                    source_context="test",
                    generator_type="test",
                ),
                BrandGenerationInsight(
                    insight_text="Insight 2",
                    confidence=0.7,
                    frequency=2,
                    last_seen=datetime.utcnow(),
                    source_context="test",
                    generator_type="test",
                ),
            ],
        )
        
        summary = memory.get_insight_summary(max_insights=2)
        assert "Insight" in summary
        assert "Brand Memory Insights" in summary
    
    def test_consolidate_insights(self):
        """Test consolidating insights from generation records."""
        memory = BrandMemory(
            brand_id="brand-1",
            brand_name="TestBrand",
        )
        
        insight = BrandGenerationInsight(
            insight_text="Duplicate insight",
            confidence=0.8,
            frequency=1,
            last_seen=datetime.utcnow(),
            source_context="test",
            generator_type="test",
        )
        
        record1 = BrandGenerationRecord(
            generation_id="gen-1",
            generator_type="swot_generator",
            brand_id="brand-1",
            brief_id=None,
            prompt="Test",
            brief_summary=None,
            output_json={},
            llm_provider="claude",
            completion_time_ms=500.0,
            extracted_insights=[insight],
        )
        
        record2 = BrandGenerationRecord(
            generation_id="gen-2",
            generator_type="swot_generator",
            brand_id="brand-1",
            brief_id=None,
            prompt="Test 2",
            brief_summary=None,
            output_json={},
            llm_provider="claude",
            completion_time_ms=600.0,
            extracted_insights=[insight],
        )
        
        memory.add_generation_record(record1)
        memory.add_generation_record(record2)
        memory.consolidate_insights()
        
        # Should have 1 consolidated insight with frequency=2
        assert len(memory.consolidated_insights) == 1
        assert memory.consolidated_insights[0].frequency == 2


class TestBrandBrainRepository:
    """Test BrandBrainRepository persistence."""
    
    def test_repository_creation(self):
        """Test creating repository with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_brand.db")
            repo = BrandBrainRepository(db_path)
            assert os.path.exists(db_path)
    
    def test_save_and_load_memory(self):
        """Test saving and loading brand memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_brand.db")
            repo = BrandBrainRepository(db_path)
            
            # Create and save memory
            memory = BrandMemory(
                brand_id="test-brand-1",
                brand_name="Test Brand",
                brand_voice_summary="Casual, playful tone",
                learned_behaviors=["Use emojis", "Short sentences"],
            )
            
            record = BrandGenerationRecord(
                generation_id="gen-1",
                generator_type="swot_generator",
                brand_id="test-brand-1",
                brief_id="brief-1",
                prompt="Generate SWOT",
                brief_summary="Tech startup",
                output_json={"strengths": ["Fast"]},
                llm_provider="claude",
                completion_time_ms=1200.0,
            )
            memory.add_generation_record(record)
            
            repo.save_memory(memory)
            
            # Load and verify
            loaded = repo.load_memory("test-brand-1")
            assert loaded is not None
            assert loaded.brand_id == "test-brand-1"
            assert loaded.brand_name == "Test Brand"
            assert len(loaded.generation_history) == 1
            assert loaded.brand_voice_summary == "Casual, playful tone"
    
    def test_get_recent_insights(self):
        """Test retrieving recent insights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_brand.db")
            repo = BrandBrainRepository(db_path)
            
            memory = BrandMemory(
                brand_id="test-brand-2",
                brand_name="Test Brand 2",
            )
            
            insight = BrandGenerationInsight(
                insight_text="Recent insight",
                confidence=0.85,
                frequency=2,
                last_seen=datetime.utcnow(),
                source_context="Recent",
                generator_type="swot_generator",
            )
            
            record = BrandGenerationRecord(
                generation_id="gen-2",
                generator_type="swot_generator",
                brand_id="test-brand-2",
                brief_id=None,
                prompt="Test",
                brief_summary=None,
                output_json={},
                llm_provider="claude",
                completion_time_ms=500.0,
                extracted_insights=[insight],
            )
            memory.add_generation_record(record)
            repo.save_memory(memory)
            
            # Retrieve recent insights
            recent = repo.get_recent_insights("test-brand-2", days=7)
            assert len(recent) > 0
    
    def test_list_brands(self):
        """Test listing all brands in repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_brand.db")
            repo = BrandBrainRepository(db_path)
            
            # Save multiple brands
            for i in range(3):
                memory = BrandMemory(
                    brand_id=f"brand-{i}",
                    brand_name=f"Brand {i}",
                )
                repo.save_memory(memory)
            
            brands = repo.list_brands()
            assert len(brands) == 3


class TestBrandBrainInsightExtractor:
    """Test automatic insight extraction from generator outputs."""
    
    def test_extract_from_swot(self):
        """Test extracting insights from SWOT analysis."""
        swot_data = {
            "strengths": [
                {"strength": "Strong brand recognition"},
                {"strength": "Innovative product"},
            ],
            "opportunities": [
                {"opportunity": "Expand to Asian markets"},
            ],
            "weaknesses": [
                {"weakness": "High costs"},
            ],
            "threats": [
                {"threat": "Increased competition"},
            ],
        }
        
        insights = BrandBrainInsightExtractor.extract_from_swot(swot_data)
        assert len(insights) > 0
        assert any("Opportunity" in i.insight_text for i in insights)
        assert any("strength" in i.insight_text for i in insights)
    
    def test_extract_from_personas(self):
        """Test extracting insights from personas."""
        personas_data = [
            {
                "name": "Tech-Savvy Tom",
                "motivation": "Stay ahead of technology trends",
                "pain_point": "Too many tools to manage",
            },
            {
                "name": "Budget-Conscious Betty",
                "motivation": "Reduce operational costs",
                "pain_point": "Limited budget for new tools",
            },
        ]
        
        insights = BrandBrainInsightExtractor.extract_from_personas(personas_data)
        assert len(insights) > 0
        assert any("motivated" in i.insight_text.lower() for i in insights)
        assert any("pain point" in i.insight_text.lower() for i in insights)
    
    def test_extract_from_social_calendar(self):
        """Test extracting insights from social calendar."""
        posts_data = [
            {
                "platform": "Instagram",
                "theme": "User testimonials",
                "hook": "Check out what our users are saying",
            },
            {
                "platform": "LinkedIn",
                "theme": "Industry insights",
                "hook": "5 trends shaping 2024",
            },
        ]
        
        insights = BrandBrainInsightExtractor.extract_from_social_calendar(posts_data)
        assert len(insights) > 0
        assert any("platform" in i.insight_text.lower() for i in insights)
    
    def test_extract_insights_dispatch(self):
        """Test insight extraction dispatch logic."""
        # Test SWOT
        swot_output = {"strengths": [{"strength": "Fast"}]}
        insights = BrandBrainInsightExtractor.extract_insights(
            swot_output,
            "swot_generator"
        )
        assert len(insights) > 0
        
        # Test personas
        persona_output = [{"name": "Person", "motivation": "Test"}]
        insights = BrandBrainInsightExtractor.extract_insights(
            persona_output,
            "persona_generator"
        )
        assert len(insights) > 0
        
        # Test social calendar
        social_output = [{"platform": "Instagram", "theme": "Test"}]
        insights = BrandBrainInsightExtractor.extract_insights(
            social_output,
            "social_calendar_generator"
        )
        assert len(insights) > 0


class TestGenerateWithBrandBrain:
    """Test the generate_with_brand_brain wrapper function."""
    
    def test_wrapper_basic_execution(self):
        """Test wrapper executes generator and extracts insights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = BrandBrainRepository(db_path)
            
            def mock_generator(**kwargs):
                return {"strengths": [{"strength": "Great product"}]}
            
            output, insights = generate_with_brand_brain(
                generator_func=mock_generator,
                brand_id="test-brand",
                generator_type="swot_generator",
                kwargs={},
                repo=repo,
            )
            
            assert output is not None
            assert isinstance(insights, list)
            assert len(insights) > 0
    
    def test_wrapper_saves_to_memory(self):
        """Test that wrapper saves generation to brand memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = BrandBrainRepository(db_path)
            
            def mock_generator(**kwargs):
                return {"personas": [{"name": "Test", "motivation": "Testing"}]}
            
            # First generation
            output, insights = generate_with_brand_brain(
                generator_func=mock_generator,
                brand_id="test-brand-2",
                generator_type="persona_generator",
                kwargs={},
                repo=repo,
            )
            
            # Verify memory was saved
            memory = repo.load_memory("test-brand-2")
            assert memory is not None
            assert len(memory.generation_history) == 1
            assert memory.total_generations == 1
    
    def test_wrapper_handles_errors_gracefully(self):
        """Test wrapper handles generator errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = BrandBrainRepository(db_path)
            
            def failing_generator(**kwargs):
                raise ValueError("Mock error")
            
            # Should raise since even fallback fails
            with pytest.raises(ValueError):
                generate_with_brand_brain(
                    generator_func=failing_generator,
                    brand_id="test-brand-3",
                    generator_type="swot_generator",
                    kwargs={},
                    repo=repo,
                )
    
    def test_convenience_functions(self):
        """Test convenience functions get_brand_memory and get_brand_insights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            repo = BrandBrainRepository(db_path)
            
            # Create and save memory with insights
            memory = BrandMemory(
                brand_id="test-brand-4",
                brand_name="Test",
            )
            
            insight = BrandGenerationInsight(
                insight_text="Test insight",
                confidence=0.9,
                frequency=1,
                last_seen=datetime.utcnow(),
                source_context="test",
                generator_type="swot_generator",
            )
            
            record = BrandGenerationRecord(
                generation_id="gen-1",
                generator_type="swot_generator",
                brand_id="test-brand-4",
                brief_id=None,
                prompt="Test",
                brief_summary=None,
                output_json={},
                llm_provider="claude",
                completion_time_ms=500.0,
                extracted_insights=[insight],
            )
            
            memory.add_generation_record(record)
            repo.save_memory(memory)
            
            # Test convenience functions
            loaded = get_brand_memory("test-brand-4", repo)
            assert loaded is not None
            assert loaded.total_generations == 1
            
            recent_insights = get_brand_insights("test-brand-4", repo=repo)
            assert len(recent_insights) > 0


class TestPhase9Integration:
    """Integration tests for Phase 9 as a whole."""
    
    def test_full_lbb_workflow(self):
        """Test complete LBB workflow: multiple generations, consolidation, insights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "lbb.db")
            repo = BrandBrainRepository(db_path)
            
            def swot_mock(**kwargs):
                return {
                    "strengths": [{"strength": "Innovation"}],
                    "opportunities": [{"opportunity": "Market expansion"}],
                }
            
            def persona_mock(**kwargs):
                return [
                    {"name": "Persona1", "motivation": "Growth"},
                ]
            
            # Generate SWOT
            output1, insights1 = generate_with_brand_brain(
                swot_mock,
                "brand-x",
                "swot_generator",
                {},
                repo=repo,
            )
            assert len(insights1) > 0
            
            # Generate personas
            output2, insights2 = generate_with_brand_brain(
                persona_mock,
                "brand-x",
                "persona_generator",
                {},
                repo=repo,
            )
            assert len(insights2) > 0
            
            # Check accumulated memory
            memory = repo.load_memory("brand-x")
            assert memory.total_generations == 2
            assert len(memory.generation_history) == 2
    
    def test_lbb_memory_persistence_across_sessions(self):
        """Test that memory persists across separate Python sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "persistent.db")
            
            # Session 1: Create and save memory
            repo1 = BrandBrainRepository(db_path)
            memory1 = BrandMemory(
                brand_id="persistent-brand",
                brand_name="Persistent Brand",
                brand_voice_summary="Professional tone",
            )
            repo1.save_memory(memory1)
            
            # Session 2: Load same memory
            repo2 = BrandBrainRepository(db_path)
            memory2 = repo2.load_memory("persistent-brand")
            
            assert memory2 is not None
            assert memory2.brand_voice_summary == "Professional tone"
