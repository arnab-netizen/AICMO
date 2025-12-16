"""
Tests for MODULE 1: Lead Capture + Attribution

Validates:
- CSV import creates ImportBatch
- Attribution fields persist correctly
- Deduplication works (email + campaign_id)
- Identity hash generation
- Batch auditing (success/fail/duplicate counts)
- File hash duplicate detection
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from aicmo.core.db import Base
from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.cam.import_models import ImportBatchDB
from aicmo.cam.lead_ingestion import (
    import_leads_from_csv,
    import_leads_from_api,
    calculate_file_hash,
    deduplicate_lead,
    ImportResult
)


@pytest.fixture
def db_session() -> Session:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_campaign(db_session: Session) -> CampaignDB:
    """Create a test campaign."""
    campaign = CampaignDB(
        name="Test Campaign",
        description="Test attribution tracking",
        active=True
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign


@pytest.fixture
def sample_csv_file() -> Path:
    """Create a temporary CSV file with test leads."""
    csv_content = """name,email,company,role,utm_campaign,utm_content,source_notes
John Doe,john@example.com,Acme Corp,CEO,Q4_2025,webinar,Met at conference
Jane Smith,jane@example.com,Beta LLC,CTO,Q4_2025,linkedin_ad,Engaged with post
Bob Johnson,bob@example.com,Gamma Inc,VP Sales,Q4_2025,email_blast,Downloaded whitepaper"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()


def test_csv_import_creates_import_batch(db_session: Session, sample_campaign: CampaignDB, sample_csv_file: Path):
    """Test that CSV import creates ImportBatch with correct metadata."""
    result = import_leads_from_csv(
        session=db_session,
        file_path=sample_csv_file,
        campaign_id=sample_campaign.id,
        venture_id="test_venture",
        uploaded_by="operator@test.com",
        source_system="manual_csv",
        source_list_name="Q4_Conference_Leads"
    )
    
    # Verify import result
    assert result.batch_id is not None
    assert result.total_rows == 3
    assert result.successful_imports == 3
    assert result.failed_imports == 0
    assert result.duplicate_skips == 0
    assert len(result.errors) == 0
    
    # Verify ImportBatch persisted correctly
    batch = db_session.query(ImportBatchDB).filter_by(id=result.batch_id).first()
    assert batch is not None
    assert batch.file_name == sample_csv_file.name
    assert batch.file_hash is not None  # SHA256 calculated
    assert batch.uploaded_by == "operator@test.com"
    assert batch.source_system == "manual_csv"
    assert batch.source_list_name == "Q4_Conference_Leads"
    assert batch.campaign_id == sample_campaign.id
    assert batch.venture_id == "test_venture"
    assert batch.total_rows == 3
    assert batch.successful_imports == 3


def test_attribution_fields_persist(db_session: Session, sample_campaign: CampaignDB, sample_csv_file: Path):
    """Test that attribution fields (UTM params, source_ref, identity_hash) are stored correctly."""
    result = import_leads_from_csv(
        session=db_session,
        file_path=sample_csv_file,
        campaign_id=sample_campaign.id,
        venture_id="test_venture",
        uploaded_by="operator@test.com",
        source_system="conference_booth"
    )
    
    # Query imported leads
    leads = db_session.query(LeadDB).filter_by(campaign_id=sample_campaign.id).all()
    assert len(leads) == 3
    
    # Check first lead attribution
    john = next((l for l in leads if l.email == "john@example.com"), None)
    assert john is not None
    assert john.name == "John Doe"
    assert john.company == "Acme Corp"
    assert john.role == "CEO"
    assert john.utm_campaign == "Q4_2025"
    assert john.utm_content == "webinar"
    assert john.notes == "Met at conference"
    assert john.source_channel == "conference_booth"
    assert john.source_ref == f"batch_{result.batch_id}_row_2"  # Row 2 (after header)
    assert john.identity_hash is not None  # SHA256 of email
    assert len(john.identity_hash) == 16  # Truncated to 16 chars
    assert john.consent_status == "UNKNOWN"  # Default
    assert john.first_touch_at is not None


def test_deduplication_by_email_and_campaign(db_session: Session, sample_campaign: CampaignDB):
    """Test that duplicate leads (same email + campaign_id) are skipped."""
    # Create existing lead
    existing_lead = LeadDB(
        campaign_id=sample_campaign.id,
        name="Existing Lead",
        email="duplicate@example.com",
        identity_hash="abc123"
    )
    db_session.add(existing_lead)
    db_session.commit()
    
    # Try to import duplicate via API
    result = import_leads_from_api(
        session=db_session,
        leads_data=[
            {"name": "Duplicate Lead", "email": "duplicate@example.com", "company": "Test Corp"}
        ],
        campaign_id=sample_campaign.id,
        venture_id="test_venture",
        uploaded_by="api_key_123",
        source_system="apollo_api"
    )
    
    # Verify duplicate was skipped
    assert result.total_rows == 1
    assert result.successful_imports == 0
    assert result.duplicate_skips == 1
    
    # Verify no new lead created
    lead_count = db_session.query(LeadDB).filter_by(email="duplicate@example.com").count()
    assert lead_count == 1  # Only original


def test_deduplication_by_identity_hash(db_session: Session, sample_campaign: CampaignDB):
    """Test that leads with same identity_hash are deduplicated cross-campaign."""
    import hashlib
    
    # Generate correct identity_hash for the email
    email = "shared@example.com"
    identity_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    
    # Create lead in campaign A
    lead_a = LeadDB(
        campaign_id=sample_campaign.id,
        name="Lead A",
        email=email,
        identity_hash=identity_hash
    )
    db_session.add(lead_a)
    db_session.commit()
    
    # Create second campaign
    campaign_b = CampaignDB(name="Campaign B", active=True)
    db_session.add(campaign_b)
    db_session.commit()
    
    # Try to import same lead into campaign B
    result = import_leads_from_api(
        session=db_session,
        leads_data=[
            {"name": "Lead B", "email": email}  # Same email -> same identity_hash
        ],
        campaign_id=campaign_b.id,
        venture_id="test_venture",
        uploaded_by="api",
        source_system="test"
    )
    
    # Verify duplicate was detected (cross-campaign deduplication)
    assert result.duplicate_skips == 1
    
    # Verify only one lead exists total
    total_leads = db_session.query(LeadDB).filter_by(email=email).count()
    assert total_leads == 1


def test_import_batch_auditable(db_session: Session, sample_campaign: CampaignDB):
    """Test that import batches track success/fail/duplicate counts for auditing."""
    # Create CSV with mixed data (valid, invalid, duplicate)
    csv_content = """name,email,company
Valid Lead,valid@example.com,Valid Corp
,missing_name@example.com,Invalid Corp
Another Lead,another@example.com,Another Corp"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = Path(f.name)
    
    try:
        # First import
        result1 = import_leads_from_csv(
            session=db_session,
            file_path=temp_path,
            campaign_id=sample_campaign.id,
            venture_id="test",
            uploaded_by="operator@test.com"
        )
        
        # Verify first import results
        assert result1.total_rows == 3
        assert result1.successful_imports == 2  # Valid + Another
        assert result1.failed_imports == 1  # Missing name
        assert result1.duplicate_skips == 0
        assert len(result1.errors) == 1
        assert "missing required field 'name'" in result1.errors[0].lower()
        
        # Verify batch persisted error log
        batch1 = db_session.query(ImportBatchDB).filter_by(id=result1.batch_id).first()
        assert batch1.error_log is not None
        assert "missing required field" in batch1.error_log.lower()
        
    finally:
        temp_path.unlink()


def test_file_hash_duplicate_detection(db_session: Session, sample_campaign: CampaignDB, sample_csv_file: Path):
    """Test that re-importing same file is detected via file hash."""
    # First import
    result1 = import_leads_from_csv(
        session=db_session,
        file_path=sample_csv_file,
        campaign_id=sample_campaign.id,
        venture_id="test",
        uploaded_by="operator@test.com"
    )
    
    assert result1.successful_imports == 3
    
    # Try to import same file again
    result2 = import_leads_from_csv(
        session=db_session,
        file_path=sample_csv_file,
        campaign_id=sample_campaign.id,
        venture_id="test",
        uploaded_by="operator@test.com"
    )
    
    # Verify second import was rejected
    assert result2.total_rows == 0
    assert result2.successful_imports == 0
    assert len(result2.errors) == 1
    assert f"already imported in batch {result1.batch_id}" in result2.errors[0].lower()
    
    # Verify only one ImportBatch exists
    batch_count = db_session.query(ImportBatchDB).count()
    assert batch_count == 1


def test_api_import_without_duplicates(db_session: Session, sample_campaign: CampaignDB):
    """Test API-based lead import (no file, direct data)."""
    leads_data = [
        {
            "name": "API Lead 1",
            "email": "api1@example.com",
            "company": "API Corp",
            "role": "Developer",
            "utm_campaign": "api_test",
            "consent_status": "CONSENTED"
        },
        {
            "name": "API Lead 2",
            "email": "api2@example.com",
            "company": "API LLC"
        }
    ]
    
    result = import_leads_from_api(
        session=db_session,
        leads_data=leads_data,
        campaign_id=sample_campaign.id,
        venture_id="test_venture",
        uploaded_by="api_key_xyz",
        source_system="apollo_api",
        source_list_name="Apollo_Q4_Export"
    )
    
    # Verify import succeeded
    assert result.total_rows == 2
    assert result.successful_imports == 2
    assert result.failed_imports == 0
    
    # Verify batch metadata
    batch = db_session.query(ImportBatchDB).filter_by(id=result.batch_id).first()
    assert batch.file_name is None  # No file for API imports
    assert batch.file_hash is None
    assert batch.source_system == "apollo_api"
    assert batch.source_list_name == "Apollo_Q4_Export"
    
    # Verify leads imported with correct attribution
    leads = db_session.query(LeadDB).filter_by(campaign_id=sample_campaign.id).all()
    assert len(leads) == 2
    
    api1 = next((l for l in leads if l.email == "api1@example.com"), None)
    assert api1.consent_status == "CONSENTED"
    assert api1.utm_campaign == "api_test"
    assert api1.source_channel == "apollo_api"


def test_identity_hash_generation(db_session: Session, sample_campaign: CampaignDB):
    """Test that identity_hash is consistently generated from email."""
    # Import lead with email
    result = import_leads_from_api(
        session=db_session,
        leads_data=[{"name": "Test Lead", "email": "TEST@EXAMPLE.COM"}],
        campaign_id=sample_campaign.id,
        venture_id="test",
        uploaded_by="test",
        source_system="test"
    )
    
    lead = db_session.query(LeadDB).filter_by(email="TEST@EXAMPLE.COM").first()
    assert lead is not None
    assert lead.identity_hash is not None
    assert len(lead.identity_hash) == 16
    
    # Verify hash is deterministic (same email -> same hash)
    import hashlib
    expected_hash = hashlib.sha256("test@example.com".encode()).hexdigest()[:16]
    assert lead.identity_hash == expected_hash


def test_missing_required_fields_fail(db_session: Session, sample_campaign: CampaignDB):
    """Test that leads without required fields are rejected."""
    result = import_leads_from_api(
        session=db_session,
        leads_data=[
            {"email": "nohname@example.com", "company": "Test"},  # Missing 'name'
            {"name": "Valid Lead", "email": "valid@example.com"}
        ],
        campaign_id=sample_campaign.id,
        venture_id="test",
        uploaded_by="test",
        source_system="test"
    )
    
    assert result.total_rows == 2
    assert result.successful_imports == 1  # Only second lead
    assert result.failed_imports == 1
    assert "missing required field 'name'" in result.errors[0].lower()
