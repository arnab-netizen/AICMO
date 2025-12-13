"""
Tests for Phase 2: Lead Harvester Engine.

Tests CSV adapter, Manual adapter, and Harvest Orchestrator.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import csv

from sqlalchemy.orm import Session

from aicmo.cam.domain import Campaign, Lead, LeadStatus, LeadSource
from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.gateways.adapters.csv_lead_source import CSVLeadSource
from aicmo.gateways.adapters.manual_lead_source import ManualLeadSource
from aicmo.cam.engine.harvest_orchestrator import (
    HarvestOrchestrator,
    HarvestMetrics,
    run_harvest_batch,
)


# ═══════════════════════════════════════════════════════════════════════════
# CSV LEAD SOURCE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestCSVLeadSource:
    """Tests for CSV lead source adapter."""
    
    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file with test leads."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False, newline=''
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=['name', 'email', 'company', 'role', 'linkedin_url']
            )
            writer.writeheader()
            writer.writerows([
                {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'company': 'Acme Corp',
                    'role': 'VP Sales',
                    'linkedin_url': 'https://linkedin.com/in/johndoe',
                },
                {
                    'name': 'Jane Smith',
                    'email': 'jane@example.com',
                    'company': 'Tech Inc',
                    'role': 'CTO',
                    'linkedin_url': 'https://linkedin.com/in/janesmith',
                },
                {
                    'name': 'Bob Johnson',
                    'email': 'bob@example.com',
                    'company': 'StartUp LLC',
                    'role': 'Founder',
                    'linkedin_url': '',
                },
            ])
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_csv_source_is_configured_when_file_exists(self, temp_csv_file):
        """Test is_configured() returns True when file exists."""
        source = CSVLeadSource(file_path=temp_csv_file)
        assert source.is_configured() is True
    
    def test_csv_source_not_configured_when_file_missing(self):
        """Test is_configured() returns False when file missing."""
        source = CSVLeadSource(file_path="/nonexistent/path.csv")
        assert source.is_configured() is False
    
    def test_csv_source_fetch_leads(self, temp_csv_file):
        """Test fetching leads from CSV file."""
        source = CSVLeadSource(file_path=temp_csv_file)
        campaign = Campaign(name="Test Campaign")
        
        leads = source.fetch_new_leads(campaign, max_leads=10)
        
        assert len(leads) == 3
        assert leads[0].name == "John Doe"
        assert leads[0].email == "john@example.com"
        assert leads[0].company == "Acme Corp"
        assert leads[0].source == LeadSource.CSV
    
    def test_csv_source_respects_max_leads(self, temp_csv_file):
        """Test max_leads limit is respected."""
        source = CSVLeadSource(file_path=temp_csv_file)
        campaign = Campaign(name="Test Campaign")
        
        leads = source.fetch_new_leads(campaign, max_leads=2)
        
        assert len(leads) == 2
    
    def test_csv_source_handles_missing_optional_fields(self, temp_csv_file):
        """Test CSV source handles missing optional fields."""
        source = CSVLeadSource(file_path=temp_csv_file)
        campaign = Campaign(name="Test Campaign")
        
        leads = source.fetch_new_leads(campaign, max_leads=10)
        
        # Bob Johnson has no LinkedIn URL (empty string in CSV)
        bob = [l for l in leads if l.name == "Bob Johnson"][0]
        assert bob.linkedin_url is None
    
    def test_csv_source_get_name(self, temp_csv_file):
        """Test adapter name."""
        source = CSVLeadSource(file_path=temp_csv_file)
        assert source.get_name() == "CSV Lead Source"


# ═══════════════════════════════════════════════════════════════════════════
# MANUAL LEAD SOURCE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestManualLeadSource:
    """Tests for manual lead source adapter."""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset manual lead queue before each test."""
        ManualLeadSource.reset_queue()
        yield
    
    def test_manual_source_always_configured(self):
        """Test manual source is always configured."""
        source = ManualLeadSource()
        assert source.is_configured() is True
    
    def test_manual_source_add_single_lead(self):
        """Test adding a single lead."""
        source = ManualLeadSource()
        
        lead_id = source.add_lead(
            name="Alice Brown",
            email="alice@example.com",
            company="Alice Inc",
            role="CEO",
        )
        
        assert lead_id == 1
        assert source.get_pending_count() == 1
    
    def test_manual_source_add_multiple_leads(self):
        """Test adding multiple leads."""
        source = ManualLeadSource()
        
        lead_ids = source.add_leads([
            {
                "name": "Alice Brown",
                "email": "alice@example.com",
                "company": "Alice Inc",
            },
            {
                "name": "Bob Wilson",
                "email": "bob@example.com",
                "company": "Bob Co",
            },
        ])
        
        assert len(lead_ids) == 2
        assert source.get_pending_count() == 2
    
    def test_manual_source_validate_required_fields(self):
        """Test validation of required fields."""
        source = ManualLeadSource()
        
        with pytest.raises(ValueError):
            source.add_lead(name="", email="test@example.com")
        
        with pytest.raises(ValueError):
            source.add_lead(name="Test User", email="invalid-email")
    
    def test_manual_source_fetch_unprocessed_leads(self):
        """Test fetching unprocessed leads."""
        source = ManualLeadSource()
        
        source.add_leads([
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ])
        
        campaign = Campaign(name="Test")
        leads = source.fetch_new_leads(campaign, max_leads=10)
        
        assert len(leads) == 2
    
    def test_manual_source_mark_processed(self):
        """Test marking leads as processed."""
        source = ManualLeadSource()
        
        source.add_leads([
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ])
        
        # Mark first lead as processed
        source.mark_as_processed([1])
        
        # Fetch should return only unprocessed
        campaign = Campaign(name="Test")
        leads = source.fetch_new_leads(campaign, max_leads=10)
        
        assert len(leads) == 1
        assert leads[0].name == "Bob"
    
    def test_manual_source_queue_stats(self):
        """Test queue statistics."""
        source = ManualLeadSource()
        
        source.add_leads([
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
            {"name": "Charlie", "email": "charlie@example.com"},
        ])
        
        source.mark_as_processed([1, 2])
        
        stats = source.get_queue_stats()
        
        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["processed"] == 2


# ═══════════════════════════════════════════════════════════════════════════
# HARVEST ORCHESTRATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestHarvestOrchestrator:
    """Tests for harvest orchestrator."""
    
    @pytest.fixture(autouse=True)
    def reset_manual_queue(self):
        """Reset manual lead queue."""
        ManualLeadSource.reset_queue()
        yield
    
    def test_harvest_metrics_duration(self):
        """Test metrics duration calculation."""
        metrics = HarvestMetrics()
        metrics.discovered = 10
        metrics.inserted = 10
        metrics.end_time = datetime.utcnow()
        
        duration = metrics.duration_seconds()
        assert isinstance(duration, float)
        assert duration >= 0
    
    def test_harvest_metrics_to_dict(self):
        """Test converting metrics to dict."""
        metrics = HarvestMetrics()
        metrics.discovered = 10
        metrics.inserted = 8
        metrics.deduplicated = 2
        metrics.sources_succeeded = 1
        metrics.end_time = datetime.utcnow()
        
        d = metrics.to_dict()
        
        assert d["discovered"] == 10
        assert d["inserted"] == 8
        assert d["deduplicated"] == 2
    
    def test_build_provider_chain(self):
        """Test building provider chain."""
        orchestrator = HarvestOrchestrator()
        
        # Mock sources
        manual_source = ManualLeadSource()
        manual_source.add_lead("Test", "test@example.com")
        
        sources = {
            "manual": manual_source,
            "unknown": None,  # Not configured
        }
        
        campaign = Campaign(name="Test")
        chain = orchestrator.build_provider_chain(campaign, sources, ["manual"])
        
        assert len(chain) == 1
        assert chain[0][0] == "manual"
    
    def test_fetch_from_source_success(self):
        """Test fetching from source successfully."""
        orchestrator = HarvestOrchestrator()
        manual_source = ManualLeadSource()
        manual_source.add_lead("Test", "test@example.com")
        
        campaign = Campaign(name="Test")
        leads, error = orchestrator.fetch_from_source(
            "manual", manual_source, campaign, 10
        )
        
        assert error is None
        assert len(leads) == 1
        assert orchestrator.metrics.sources_succeeded == 1
    
    def test_fetch_from_source_failure(self):
        """Test handling source fetch failure."""
        orchestrator = HarvestOrchestrator()
        
        # Create a mock adapter that fails
        class FailingAdapter:
            def is_configured(self):
                return True
            
            def fetch_new_leads(self, campaign, max_leads):
                raise Exception("API Error")
        
        adapter = FailingAdapter()
        campaign = Campaign(name="Test")
        
        leads, error = orchestrator.fetch_from_source("failing", adapter, campaign, 10)
        
        assert error is not None
        assert len(leads) == 0
        assert orchestrator.metrics.sources_failed == 1


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestHarvestIntegration:
    """Integration tests for harvest pipeline."""
    
    @pytest.fixture(autouse=True)
    def reset_manual_queue(self):
        """Reset manual lead queue."""
        ManualLeadSource.reset_queue()
        yield
    
    def test_harvest_with_manual_source(self, db):
        """Test harvesting with manual lead source."""
        # Create campaign
        campaign_db = CampaignDB(name="Test Campaign Harvest 1", active=True)
        db.add(campaign_db)
        db.commit()
        
        # Add leads to manual source
        manual_source = ManualLeadSource()
        manual_source.add_leads([
            {"name": "Alice", "email": "alice@example.com", "company": "Alice Inc"},
            {"name": "Bob", "email": "bob@example.com", "company": "Bob Co"},
        ])
        
        # Create provider chain
        sources = {"manual": manual_source}
        campaign = Campaign(id=campaign_db.id, name=campaign_db.name)
        
        orchestrator = HarvestOrchestrator()
        chain = orchestrator.build_provider_chain(campaign, sources, ["manual"])
        
        # Run harvest
        metrics = orchestrator.harvest_with_fallback(
            db, campaign, campaign_db, chain, max_leads=10
        )
        
        # Verify results
        assert metrics.discovered == 2
        assert metrics.inserted == 2
        assert metrics.deduplicated == 0
        
        # Verify leads in database
        leads = db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_db.id
        ).all()
        
        assert len(leads) == 2
        assert leads[0].source == LeadSource.MANUAL
        assert leads[0].status == LeadStatus.NEW
    
    def test_harvest_deduplication(self, db):
        """Test deduplication during harvest."""
        # Create campaign with existing lead
        campaign_db = CampaignDB(name="Test Campaign Dedup", active=True)
        db.add(campaign_db)
        db.commit()
        
        # Add existing lead
        existing_lead = LeadDB(
            campaign_id=campaign_db.id,
            name="Alice",
            email="alice@example.com",
            status=LeadStatus.NEW,
            source=LeadSource.MANUAL,
        )
        db.add(existing_lead)
        db.commit()
        
        # Add leads (one duplicate, one new)
        manual_source = ManualLeadSource()
        manual_source.add_leads([
            {"name": "Alice", "email": "alice@example.com"},  # Duplicate
            {"name": "Charlie", "email": "charlie@example.com"},  # New
        ])
        
        # Run harvest
        sources = {"manual": manual_source}
        campaign = Campaign(id=campaign_db.id, name=campaign_db.name)
        
        orchestrator = HarvestOrchestrator()
        chain = orchestrator.build_provider_chain(campaign, sources, ["manual"])
        
        metrics = orchestrator.harvest_with_fallback(
            db, campaign, campaign_db, chain, max_leads=10
        )
        
        # Verify deduplication
        assert metrics.discovered == 2
        assert metrics.deduplicated == 1
        assert metrics.inserted == 1
        
        # Verify only new lead in DB
        leads = db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_db.id
        ).all()
        
        assert len(leads) == 2  # 1 existing + 1 newly inserted
