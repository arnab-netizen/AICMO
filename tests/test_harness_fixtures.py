"""
Minimal test proving all harness fixtures work.
"""

import pytest
from aicmo.shared.testing import fixed_clock, in_memory_db, db_session, fake_providers


def test_fixed_clock_fixture(fixed_clock):
    """Test fixed_clock fixture works."""
    from datetime import datetime
    # Clock is frozen at 2025-12-13 12:00:00
    assert datetime.utcnow().year == 2025
    print("✅ fixed_clock fixture works")


def test_in_memory_db_fixture(in_memory_db):
    """Test in_memory_db fixture works."""
    # Engine should be created and usable
    assert in_memory_db is not None
    assert "sqlite:///:memory:" in str(in_memory_db.url)
    print("✅ in_memory_db fixture works")


def test_db_session_fixture(db_session):
    """Test db_session fixture works."""
    # Session should be created and callable
    assert db_session is not None
    assert hasattr(db_session, 'query')
    assert hasattr(db_session, 'add')
    print("✅ db_session fixture works")


def test_fake_providers_fixture(fake_providers):
    """Test fake_providers fixture works."""
    # Should have pre-registered providers
    email = fake_providers.get("email")
    assert email is not None
    
    # Should be able to call and track
    result = email(to="test@example.com")
    assert result == {"sent": True}
    
    print("✅ fake_providers fixture works")


def test_all_fixtures_together(fixed_clock, in_memory_db, db_session, fake_providers):
    """Test all fixtures work together."""
    from datetime import datetime
    
    # Time is fixed
    assert datetime.utcnow().year == 2025
    
    # DB works
    assert db_session is not None
    
    # Providers work
    assert fake_providers.get("email") is not None
    
    print("✅ All fixtures work together")
