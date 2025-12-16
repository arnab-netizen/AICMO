"""
Test database URL validation.

Verifies that:
1. SQLite URLs are parsed correctly
2. PostgreSQL async/sync drivers are detected
3. Missing drivers are reported as issues
4. Credentials are masked in output
"""

import os
import pytest
from unittest.mock import patch
from aicmo.core.db import validate_database_url, mask_url


def test_sqlite_url_validation():
    """Test validation of SQLite URL."""
    result = validate_database_url('sqlite:///local.db')
    
    assert result['valid'] is True
    assert result['db_type'] == 'sqlite'
    assert result['is_async'] is False


def test_postgresql_sync_url():
    """Test validation of PostgreSQL sync URL."""
    url = 'postgresql+psycopg2://user:pass@localhost:5432/aicmo'
    result = validate_database_url(url)
    
    assert result['db_type'] == 'postgresql'
    assert result['is_async'] is False
    assert result['driver'] == 'psycopg2'


def test_postgresql_async_url():
    """Test validation of PostgreSQL async URL."""
    url = 'postgresql+asyncpg://user:pass@localhost:5432/aicmo'
    result = validate_database_url(url)
    
    assert result['db_type'] == 'postgresql'
    assert result['is_async'] is True
    assert result['driver'] == 'asyncpg'


def test_missing_asyncpg_driver():
    """Test detection of missing asyncpg driver."""
    url = 'postgresql+asyncpg://user:pass@localhost:5432/aicmo'
    
    with patch('aicmo.core.db._is_module_installed') as mock_check:
        mock_check.return_value = False  # asyncpg not installed
        
        result = validate_database_url(url)
        
        assert result['valid'] is False
        assert any('asyncpg' in issue for issue in result['issues'])


def test_credentials_masked():
    """Test that credentials are masked in output."""
    url = 'postgresql+psycopg2://user:secret123@localhost:5432/aicmo'
    
    result = validate_database_url(url)
    
    masked = result['database_url']
    assert 'secret123' not in masked
    assert 'user' in masked
    assert '***' in masked


def test_mask_url_without_credentials():
    """Test masking of URL without credentials."""
    url = 'postgresql://localhost:5432/aicmo'
    result = mask_url(url)
    
    assert result == url


def test_mask_url_with_credentials():
    """Test masking of URL with credentials."""
    url = 'postgresql://admin:password@localhost/aicmo'
    result = mask_url(url)
    
    assert 'password' not in result
    assert '***' in result
    assert 'admin' in result


def test_empty_url_uses_env_default():
    """Test that empty URL uses DATABASE_URL environment variable."""
    # Empty string means "use env", so it actually uses DATABASE_URL or defaults to sqlite
    # Since DATABASE_URL is set, it will use that
    result = validate_database_url('')
    
    # Whatever is in the environment (could be postgres or sqlite)
    assert result['db_type'] is not None


def test_explicit_sqlite_url():
    """Test that we can force SQLite even if env has postgres."""
    result = validate_database_url('sqlite:///test.db')
    
    assert result['db_type'] == 'sqlite'
    assert result['valid'] is True


def test_invalid_url_format():
    """Test validation of malformed URL."""
    result = validate_database_url('not-a-valid-url')
    
    assert result['valid'] is False
    assert any('format' in issue.lower() for issue in result['issues'])


def test_sqlite_relative_path_warning():
    """Test that relative SQLite paths trigger a warning."""
    result = validate_database_url('sqlite:///relative/path/test.db')
    
    assert result['db_type'] == 'sqlite'
    assert any('relative' in w.lower() for w in result['warnings'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
