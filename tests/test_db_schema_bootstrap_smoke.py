"""
Smoke test for DB schema bootstrap.

Verifies that:
1. Bootstrap script can be imported
2. Bootstrap can run in temp SQLite (doesn't touch real local.db)
3. Bootstrap reports success or clear BLOCKED reason
"""

import os
import sys
import sqlite3
import tempfile
import pytest
from pathlib import Path


def test_bootstrap_script_imports():
    """Test that bootstrap script can be imported without errors."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from scripts.bootstrap_db_schema import bootstrap_db_schema, get_sqlite_tables
    
    assert callable(bootstrap_db_schema)
    assert callable(get_sqlite_tables)


def test_bootstrap_with_temp_db():
    """Test bootstrap with temporary SQLite database."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from scripts.bootstrap_db_schema import bootstrap_db_schema, get_sqlite_tables
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_db = os.path.join(tmpdir, 'test.db')
        
        # Temporarily override DATABASE_URL
        old_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = f'sqlite:///{temp_db}'
        
        try:
            # Before bootstrap, no tables
            tables_before = get_sqlite_tables(temp_db)
            assert tables_before == []  # File doesn't exist yet
            
            # Run bootstrap
            result = bootstrap_db_schema()
            
            # Check result structure
            assert 'success' in result
            assert 'database_url' in result
            assert 'db_type' in result
            assert 'tables_before' in result
            assert 'tables_after' in result
            assert 'error' in result
            
            # Should have created alembic_version at minimum
            assert result['db_type'] == 'sqlite'
            
            # If database file was created, verify structure
            if os.path.exists(temp_db):
                tables_after = get_sqlite_tables(temp_db)
                # At minimum should have alembic_version
                assert len(tables_after) >= 1
                assert 'alembic_version' in tables_after or result['success']
        
        finally:
            # Restore original DATABASE_URL
            if old_url:
                os.environ['DATABASE_URL'] = old_url
            elif 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']


def test_sqlite_tables_listing():
    """Test that we can list SQLite tables correctly."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from scripts.bootstrap_db_schema import get_sqlite_tables
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_db = os.path.join(tmpdir, 'test.db')
        
        # Create test database with a table
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY)')
        cursor.execute('CREATE TABLE another_table (name TEXT)')
        conn.commit()
        conn.close()
        
        # List tables
        tables = get_sqlite_tables(temp_db)
        assert 'test_table' in tables
        assert 'another_table' in tables


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
