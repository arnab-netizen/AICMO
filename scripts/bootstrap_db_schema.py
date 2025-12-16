#!/usr/bin/env python3
"""
Bootstrap database schema for AICMO.

Purpose:
  Ensure application schema is initialized for local runs and tests.
  Does NOT run automatically on import; only via explicit script/CLI invocation.

Behavior:
  1. Detects configured database URL (LOCAL/SQLITE by default)
  2. Runs alembic upgrade head programmatically
  3. Verifies schema was created (tables > just alembic_version)
  4. Reports results with masked credentials
  5. Exits non-zero if tables still missing

Usage:
  python scripts/bootstrap_db_schema.py
  or from Python:
    from scripts.bootstrap_db_schema import bootstrap_db_schema
    status = bootstrap_db_schema()  # returns dict with success bool
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from alembic.config import Config
from alembic.command import upgrade

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get configured database URL (supports both sync and async drivers).
    
    Returns:
      Configured DATABASE_URL or local sqlite default
    """
    url = os.getenv('DATABASE_URL', 'sqlite:///local.db')
    return url


def mask_database_url(url: str) -> str:
    """Mask credentials in database URL for safe display."""
    if '://' not in url:
        return url
    
    scheme, rest = url.split('://', 1)
    if '@' in rest:
        creds, host_part = rest.rsplit('@', 1)
        user, _ = creds.split(':', 1) if ':' in creds else (creds, '')
        return f"{scheme}://{user}:***@{host_part}"
    return url


def get_sqlite_tables(db_path: str) -> List[str]:
    """Get list of application tables in SQLite database (excluding internal)."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        logger.error(f"Failed to query SQLite: {e}")
        return []


def bootstrap_db_schema() -> Dict:
    """
    Bootstrap database schema by running alembic migrations.
    
    Returns:
      Dict with keys:
        - success: bool (True if schema created)
        - database_url: str (masked)
        - db_type: str (sqlite or postgresql)
        - tables_before: List[str]
        - tables_after: List[str]
        - error: str or None
    """
    result = {
        'success': False,
        'database_url': None,
        'db_type': None,
        'tables_before': [],
        'tables_after': [],
        'error': None,
    }
    
    # Get database URL
    db_url = get_database_url()
    result['database_url'] = mask_database_url(db_url)
    
    # Determine DB type
    if 'sqlite' in db_url:
        result['db_type'] = 'sqlite'
        db_path = db_url.replace('sqlite:///', '')
        
        # Get tables BEFORE migration
        result['tables_before'] = get_sqlite_tables(db_path)
        
        # Run alembic upgrade
        try:
            alembic_config = Config('alembic.ini')
            alembic_config.set_main_option('sqlalchemy.url', db_url)
            upgrade(alembic_config, 'head')
            print(f"✓ Ran alembic upgrade head")
        except Exception as e:
            result['error'] = f"Alembic upgrade failed: {str(e)}"
            print(f"✗ Alembic upgrade failed: {e}")
            return result
        
        # Get tables AFTER migration
        result['tables_after'] = get_sqlite_tables(db_path)
        
        # Check success: must have more than just alembic_version
        if len(result['tables_after']) > 1:
            result['success'] = True
            print(f"✓ Schema initialized. Tables: {result['tables_after']}")
        else:
            result['error'] = f"Schema incomplete. Found only: {result['tables_after']}"
            print(f"✗ Schema incomplete. Found only: {result['tables_after']}")
    
    else:
        # PostgreSQL or other
        result['db_type'] = 'postgresql' if 'postgres' in db_url else 'unknown'
        result['error'] = f"PostgreSQL bootstrap not yet implemented. URL: {result['database_url']}"
        print(f"⚠️  {result['error']}")
        return result
    
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("AICMO Database Schema Bootstrap")
    print("=" * 80)
    print()
    
    result = bootstrap_db_schema()
    
    print()
    print(f"Database Type:  {result['db_type']}")
    print(f"Database URL:   {result['database_url']}")
    print(f"Tables Before:  {result['tables_before']}")
    print(f"Tables After:   {result['tables_after']}")
    
    if result['error']:
        print(f"Error:          {result['error']}")
        sys.exit(1)
    
    if result['success']:
        print()
        print("✓ SUCCESS: Database schema is ready for application use")
        sys.exit(0)
    else:
        print()
        print("✗ FAILED: Schema initialization incomplete")
        sys.exit(1)
