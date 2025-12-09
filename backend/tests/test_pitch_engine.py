"""
Tests for Pitch & Proposal Engine (Stage P).

Validates pitch deck and proposal generation with learning hooks.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from aicmo.pitch.domain import (
    Prospect,
    PitchDeck,
    PitchSection,
    Proposal,
    PitchOutcome,
)
from aicmo.pitch.service import (
    generate_pitch_deck,
    generate_proposal,
    record_pitch_outcome,
)
from aicmo.learning.event_types import EventType


class TestProspectDomain:
    """Test Prospect domain model."""
    
    def test_prospect_minimal(self):
        """Prospect can be created with minimal fields."""
        prospect = Prospect(
            name="John Doe",
            company="Acme Corp",
            industry="SaaS"
        )
        
        assert prospect.name == "John Doe"
        assert prospect.company == "Acme Corp"
        assert prospect.industry == "SaaS"
        assert prospect.stage == "prospect"
        assert isinstance(prospect.pain_points, list)
        assert isinstance(prospect.goals, list)
    
    def test_prospect_full(self):
        """Prospect can be created with all fields."""
        prospect = Prospect(
            id=123,
            name="Jane Smith",
            company="TechStart Inc",
            industry="B2B SaaS",
            company_size="50-200 employees",
            region="North America",
            pain_points=["Low brand awareness", "No content strategy"],
            goals=["Increase leads by 50%", "Launch new product"],
            budget_range="$50k-$100k",
            timeline="Q1 2026",
            discovery_notes="Great fit, urgent need",
            source="referral",
            stage="qualified"
        )
        
        assert prospect.id == 123
        assert len(prospect.pain_points) == 2
        assert len(prospect.goals) == 2
        assert prospect.stage == "qualified"


class TestPitchDeckDomain:
    """Test PitchDeck domain model."""
    
    def test_pitch_deck_minimal(self):
        """PitchDeck can be created with minimal fields."""
        deck = PitchDeck(
            title="Test Pitch",
            sections=[]
        )
        
        assert deck.title == "Test Pitch"
        assert isinstance(deck.sections, list)
        assert deck.version == 1
        assert deck.target_duration_minutes == 30
    
    def test_pitch_deck_with_sections(self):
        """PitchDeck can contain multiple sections."""
        sections = [
            PitchSection(title="Problem", content="Pain points", order=1),
            PitchSection(title="Solution", content="Our approach", order=2),
        ]
        
        deck = PitchDeck(
            title="Full Pitch",
            sections=sections,
            key_benefits=["Benefit 1", "Benefit 2"]
        )
        
        assert len(deck.sections) == 2
        assert deck.sections[0].title == "Problem"
        assert len(deck.key_benefits) == 2


class TestProposalDomain:
    """Test Proposal domain model."""
    
    def test_proposal_minimal(self):
        """Proposal can be created with minimal fields."""
        proposal = Proposal(
            title="Test Proposal",
            executive_summary="Summary here"
        )
        
        assert proposal.title == "Test Proposal"
        assert proposal.status == "draft"
        assert proposal.version == 1
    
    def test_proposal_with_pricing(self):
        """Proposal can contain scope and pricing."""
        from aicmo.pitch.domain import ProposalScope, ProposalPricing
        
        proposal = Proposal(
            title="Full Proposal",
            executive_summary="Complete proposal",
            scope=[
                ProposalScope(
                    deliverable="Strategy",
                    description="Marketing strategy",
                    timeline="Week 1"
                )
            ],
            pricing=[
                ProposalPricing(
                    item="Strategy",
                    amount=15000.0,
                    unit="one-time"
                )
            ],
            total_amount=15000.0
        )
        
        assert len(proposal.scope) == 1
        assert len(proposal.pricing) == 1
        assert proposal.total_amount == 15000.0


class TestPitchDeckGeneration:
    """Test pitch deck generation service."""
    
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
    def sample_prospect(self):
        """Create sample prospect for testing."""
        return Prospect(
            id=1,
            name="Test Contact",
            company="Test Company",
            industry="Technology",
            pain_points=["Low awareness", "No strategy"],
            goals=["Grow leads", "Launch product"],
            budget_range="$50k-$100k",
            timeline="Q1 2026"
        )
    
    def test_generate_pitch_deck_returns_deck(self, temp_db, sample_prospect):
        """generate_pitch_deck returns a PitchDeck object."""
        deck = generate_pitch_deck(sample_prospect)
        
        assert isinstance(deck, PitchDeck)
        assert deck.title
        assert deck.prospect_id == sample_prospect.id
        assert len(deck.sections) > 0
    
    def test_generate_pitch_deck_has_sections(self, temp_db, sample_prospect):
        """Generated pitch deck contains structured sections."""
        deck = generate_pitch_deck(sample_prospect)
        
        # Should have standard sections
        assert len(deck.sections) >= 3
        section_titles = [s.title for s in deck.sections]
        assert any("Problem" in title for title in section_titles)
        assert any("Solution" in title for title in section_titles)
    
    def test_generate_pitch_deck_logs_events(self, temp_db, sample_prospect):
        """Pitch deck generation logs learning events."""
        with patch('aicmo.pitch.service.log_event') as mock_log:
            generate_pitch_deck(sample_prospect)
            
            # Should log at least 2 events: PITCH_DECK_GENERATED and PITCH_CREATED
            assert mock_log.call_count >= 2
            
            # Verify PITCH_DECK_GENERATED event
            calls = [call[0][0] for call in mock_log.call_args_list]
            assert EventType.PITCH_DECK_GENERATED.value in calls
            assert EventType.PITCH_CREATED.value in calls
    
    def test_generate_pitch_deck_includes_prospect_context(self, temp_db, sample_prospect):
        """Pitch deck incorporates prospect pain points and goals."""
        deck = generate_pitch_deck(sample_prospect)
        
        # Check that content references prospect info
        all_content = " ".join(s.content for s in deck.sections).lower()
        
        # Should mention company or industry
        assert sample_prospect.company.lower() in deck.title.lower() or \
               sample_prospect.industry.lower() in all_content
    
    def test_generate_pitch_deck_with_minimal_prospect(self, temp_db):
        """Pitch deck can be generated even with minimal prospect info."""
        minimal_prospect = Prospect(
            name="Minimal",
            company="MinCo",
            industry="Retail"
        )
        
        deck = generate_pitch_deck(minimal_prospect)
        
        assert isinstance(deck, PitchDeck)
        assert len(deck.sections) > 0


class TestProposalGeneration:
    """Test proposal generation service."""
    
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
    def sample_prospect(self):
        """Create sample prospect for testing."""
        return Prospect(
            id=2,
            name="Proposal Test",
            company="PropCo",
            industry="E-commerce",
            budget_range="$75k",
            timeline="2 months"
        )
    
    def test_generate_proposal_returns_proposal(self, temp_db, sample_prospect):
        """generate_proposal returns a Proposal object."""
        proposal = generate_proposal(sample_prospect)
        
        assert isinstance(proposal, Proposal)
        assert proposal.title
        assert proposal.prospect_id == sample_prospect.id
    
    def test_generate_proposal_has_scope_and_pricing(self, temp_db, sample_prospect):
        """Generated proposal contains scope and pricing."""
        proposal = generate_proposal(sample_prospect)
        
        assert len(proposal.scope) > 0
        assert len(proposal.pricing) > 0
        assert proposal.total_amount is not None
        assert proposal.total_amount > 0
    
    def test_generate_proposal_calculates_total(self, temp_db, sample_prospect):
        """Proposal total matches sum of pricing items."""
        proposal = generate_proposal(sample_prospect)
        
        expected_total = sum(item.amount for item in proposal.pricing)
        assert proposal.total_amount == expected_total
    
    def test_generate_proposal_logs_event(self, temp_db, sample_prospect):
        """Proposal generation logs learning event."""
        with patch('aicmo.pitch.service.log_event') as mock_log:
            generate_proposal(sample_prospect)
            
            # Should log PROPOSAL_GENERATED event
            mock_log.assert_called()
            calls = [call[0][0] for call in mock_log.call_args_list]
            assert EventType.PROPOSAL_GENERATED.value in calls
    
    def test_generate_proposal_with_pitch_deck(self, temp_db, sample_prospect):
        """Proposal can reference an associated pitch deck."""
        deck = generate_pitch_deck(sample_prospect)
        proposal = generate_proposal(sample_prospect, pitch_deck=deck)
        
        assert isinstance(proposal, Proposal)
        # Verify event logged with pitch_deck context
        with patch('aicmo.pitch.service.log_event') as mock_log:
            generate_proposal(sample_prospect, pitch_deck=deck)
            
            # Find the PROPOSAL_GENERATED call
            for call in mock_log.call_args_list:
                if call[0][0] == EventType.PROPOSAL_GENERATED.value:
                    details = call[1].get('details', {})
                    assert details.get('has_pitch_deck') is True


class TestPitchOutcome:
    """Test pitch outcome recording."""
    
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
    
    def test_record_pitch_won(self, temp_db):
        """Recording a won pitch logs PITCH_WON event."""
        outcome = PitchOutcome(
            prospect_id=1,
            outcome="won",
            deal_value=75000.0,
            win_factors=["Strong case studies", "Competitive pricing"]
        )
        
        with patch('aicmo.pitch.service.log_event') as mock_log:
            record_pitch_outcome(outcome)
            
            # Should log PITCH_WON
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == EventType.PITCH_WON.value
            
            # Verify details include deal value and win factors
            details = mock_log.call_args[1]['details']
            assert details['deal_value'] == 75000.0
            assert 'win_factors' in details
    
    def test_record_pitch_lost(self, temp_db):
        """Recording a lost pitch logs PITCH_LOST event."""
        outcome = PitchOutcome(
            prospect_id=2,
            outcome="lost",
            loss_reasons=["Price too high", "Timing not right"],
            competitor="CompetitorX"
        )
        
        with patch('aicmo.pitch.service.log_event') as mock_log:
            record_pitch_outcome(outcome)
            
            # Should log PITCH_LOST
            mock_log.assert_called_once()
            assert mock_log.call_args[0][0] == EventType.PITCH_LOST.value
            
            # Verify details include loss reasons
            details = mock_log.call_args[1]['details']
            assert 'loss_reasons' in details
            assert details['competitor'] == "CompetitorX"
    
    def test_record_pitch_outcome_for_learning(self, temp_db):
        """Pitch outcomes contain learning data."""
        won_outcome = PitchOutcome(
            prospect_id=3,
            outcome="won",
            deal_value=100000.0,
            win_factors=["Quick turnaround", "Industry expertise"],
            feedback="Impressed by our process"
        )
        
        # Should not raise
        record_pitch_outcome(won_outcome)


class TestPitchEngineIntegration:
    """Integration tests for complete pitch workflow."""
    
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
    
    def test_complete_pitch_to_proposal_workflow(self, temp_db):
        """Complete workflow: prospect → pitch → proposal → outcome."""
        # 1. Create prospect
        prospect = Prospect(
            id=999,
            name="Integration Test",
            company="IntegrationCo",
            industry="FinTech",
            pain_points=["Legacy systems", "Slow growth"],
            goals=["Modernize brand", "2x leads"],
            budget_range="$100k-$150k",
            timeline="Q1 2026"
        )
        
        # 2. Generate pitch deck
        deck = generate_pitch_deck(prospect)
        assert isinstance(deck, PitchDeck)
        assert deck.prospect_id == prospect.id
        
        # 3. Generate proposal
        proposal = generate_proposal(prospect, pitch_deck=deck)
        assert isinstance(proposal, Proposal)
        assert proposal.prospect_id == prospect.id
        
        # 4. Record outcome
        outcome = PitchOutcome(
            prospect_id=prospect.id,
            pitch_deck_id=1,  # Assuming deck would have ID after DB save
            proposal_id=1,    # Assuming proposal would have ID after DB save
            outcome="won",
            deal_value=125000.0,
            win_factors=["Strong fit", "Competitive pricing", "Fast turnaround"]
        )
        
        # Should complete without errors
        record_pitch_outcome(outcome)
    
    def test_pitch_engine_logs_all_events(self, temp_db):
        """Full workflow logs all expected events."""
        prospect = Prospect(
            id=888,
            name="Event Test",
            company="EventCo",
            industry="SaaS"
        )
        
        with patch('aicmo.pitch.service.log_event') as mock_log:
            # Generate pitch and proposal
            deck = generate_pitch_deck(prospect)
            proposal = generate_proposal(prospect, pitch_deck=deck)
            
            outcome = PitchOutcome(
                prospect_id=prospect.id,
                outcome="won",
                deal_value=50000.0
            )
            record_pitch_outcome(outcome)
            
            # Verify all expected events were logged
            event_types = [call[0][0] for call in mock_log.call_args_list]
            
            assert EventType.PITCH_CREATED.value in event_types
            assert EventType.PITCH_DECK_GENERATED.value in event_types
            assert EventType.PROPOSAL_GENERATED.value in event_types
            assert EventType.PITCH_WON.value in event_types
