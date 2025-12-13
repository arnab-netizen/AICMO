"""
Step 2: Validate test harness is not 'false green'.

This test proves the in-memory database fixture actually creates real tables,
not just a hollow SQLite file.
"""

import pytest
from sqlalchemy import inspect, text


def test_in_memory_db_has_real_tables(in_memory_db):
    """
    Prove the in-memory DB fixture creates actual tables.
    
    Must assert that at least one known table exists.
    """
    inspector = inspect(in_memory_db)
    tables = inspector.get_table_names()
    
    # Assert we have tables
    assert len(tables) > 0, (
        "In-memory database has no tables! "
        "Test harness is false-green. "
        f"Check that aicmo.cam.db_models is imported in aicmo/shared/testing.py"
    )
    
    # Assert we know some expected tables
    expected_tables = {
        "cam_campaigns",
        "cam_leads",
        "cam_outreach_attempts",
        "cam_discovered_profiles",
    }
    
    actual_tables = set(tables)
    found_tables = expected_tables & actual_tables
    
    assert found_tables, (
        f"Expected at least one of {expected_tables} but found: {actual_tables}"
    )
    
    print(f"✅ In-memory DB has {len(tables)} real tables: {sorted(tables)}")


def test_in_memory_db_can_query_tables(in_memory_db, db_session):
    """
    Prove we can actually query the in-memory tables.
    """
    # Get the number of columns in cam_leads table
    inspector = inspect(in_memory_db)
    columns = inspector.get_columns("cam_leads")
    
    assert len(columns) > 0, "cam_leads table exists but has no columns"
    
    # Verify we can write and read
    result = db_session.execute(
        text("SELECT COUNT(*) FROM cam_leads")
    ).scalar()
    
    assert result == 0, "cam_leads should start empty"
    
    print(f"✅ cam_leads table has {len(columns)} columns and is queryable")


def test_in_memory_db_foreign_keys_enabled(in_memory_db):
    """
    Prove that foreign key constraints are enabled in the test DB.
    """
    with in_memory_db.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert result == 1, "Foreign key constraints must be enabled for realistic testing"
    
    print("✅ Foreign key constraints are enabled")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
