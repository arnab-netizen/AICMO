"""
CAM lead sources tests.

Tests CSV import and lead persistence.
"""

import pytest
import tempfile
import csv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.cam.domain import LeadSource, LeadStatus
from aicmo.cam.sources import CSVSourceConfig, load_leads_from_csv, persist_leads


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing CAM tables only."""
    engine = create_engine("sqlite:///:memory:")
    
    # Create only CAM tables
    CampaignDB.__table__.create(engine, checkfirst=True)
    LeadDB.__table__.create(engine, checkfirst=True)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestCAMSources:
    """Test CAM lead sources."""
    
    def test_load_leads_from_csv(self, tmp_path):
        """Test loading leads from a CSV file."""
        # Create a temp CSV file
        csv_path = tmp_path / "test_leads.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "company", "role", "email", "linkedin_url"])
            writer.writeheader()
            writer.writerow({
                "name": "John Doe",
                "company": "Acme Corp",
                "role": "CEO",
                "email": "john@acme.com",
                "linkedin_url": "https://linkedin.com/in/johndoe",
            })
            writer.writerow({
                "name": "Jane Smith",
                "company": "TechCo",
                "role": "CTO",
                "email": "jane@techco.com",
                "linkedin_url": "",
            })
        
        # Load leads
        config = CSVSourceConfig(path=str(csv_path), campaign_id=1)
        leads = load_leads_from_csv(config)
        
        assert len(leads) == 2
        assert leads[0].name == "John Doe"
        assert leads[0].company == "Acme Corp"
        assert leads[0].role == "CEO"
        assert leads[0].email == "john@acme.com"
        assert leads[0].source == LeadSource.CSV
        assert leads[0].campaign_id == 1
        
        assert leads[1].name == "Jane Smith"
        assert leads[1].company == "TechCo"
    
    def test_load_leads_from_csv_file_not_found(self):
        """Test error handling when CSV file doesn't exist."""
        config = CSVSourceConfig(path="/nonexistent/file.csv", campaign_id=1)
        
        with pytest.raises(FileNotFoundError):
            load_leads_from_csv(config)
    
    def test_load_leads_with_alternate_column_names(self, tmp_path):
        """Test CSV loading with alternate column names (full_name, title)."""
        csv_path = tmp_path / "alt_leads.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["full_name", "title"])
            writer.writeheader()
            writer.writerow({
                "full_name": "Bob Johnson",
                "title": "VP Sales",
            })
        
        config = CSVSourceConfig(path=str(csv_path), campaign_id=2)
        leads = load_leads_from_csv(config)
        
        assert len(leads) == 1
        assert leads[0].name == "Bob Johnson"
        assert leads[0].role == "VP Sales"
        assert leads[0].campaign_id == 2
    
    def test_persist_leads(self, db_session):
        """Test persisting leads to database."""
        # Create a campaign first
        campaign = CampaignDB(name="Test Campaign")
        db_session.add(campaign)
        db_session.commit()
        
        # Create leads
        from aicmo.cam.domain import Lead
        leads = [
            Lead(
                campaign_id=campaign.id,
                name="Alice Brown",
                company="StartupX",
                role="Founder",
                email="alice@startupx.com",
                source=LeadSource.CSV,
            ),
            Lead(
                campaign_id=campaign.id,
                name="Charlie Davis",
                company="ScaleUp",
                email="charlie@scaleup.com",
                source=LeadSource.MANUAL,
            ),
        ]
        
        # Persist
        rows = persist_leads(db_session, leads)
        
        assert len(rows) == 2
        assert rows[0].id is not None
        assert rows[0].name == "Alice Brown"
        assert rows[0].company == "StartupX"
        assert rows[0].status == LeadStatus.NEW
        
        assert rows[1].id is not None
        assert rows[1].name == "Charlie Davis"
        assert rows[1].source == LeadSource.MANUAL
    
    def test_csv_to_db_full_workflow(self, tmp_path, db_session):
        """Test complete workflow: CSV → Domain models → DB."""
        # Create campaign
        campaign = CampaignDB(name="Integration Test Campaign")
        db_session.add(campaign)
        db_session.commit()
        
        # Create CSV
        csv_path = tmp_path / "workflow_leads.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email"])
            writer.writeheader()
            writer.writerow({"name": "Test Lead 1", "email": "test1@example.com"})
            writer.writerow({"name": "Test Lead 2", "email": "test2@example.com"})
        
        # Load from CSV
        config = CSVSourceConfig(path=str(csv_path), campaign_id=campaign.id)
        leads = load_leads_from_csv(config)
        
        # Persist to DB
        rows = persist_leads(db_session, leads)
        
        # Query back from DB
        db_leads = db_session.query(LeadDB).filter_by(campaign_id=campaign.id).all()
        
        assert len(db_leads) == 2
        assert db_leads[0].name == "Test Lead 1"
        assert db_leads[0].email == "test1@example.com"
        assert db_leads[1].name == "Test Lead 2"
