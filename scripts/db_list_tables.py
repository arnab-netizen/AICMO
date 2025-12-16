#!/usr/bin/env python3
"""
List database tables for debugging and schema verification.

Purpose:
  Display all tables in the configured database with masked credentials.
  Used to verify schema migration success.

Usage:
  python scripts/db_list_tables.py

Output:
  Prints database URL (masked) and list of all tables.
  Exits 0 if successful, 1 if DB unavailable.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Get configured database URL."""
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
    """Get list of all tables in SQLite database."""
    try:
        # Handle both absolute and relative paths
        if db_path.startswith('sqlite:///'):
            # Convert sqlite:/// URL to file path
            # sqlite:///local.db → local.db
            # sqlite:////tmp/aol.db → /tmp/aol.db
            path_part = db_path[10:]  # Remove sqlite:///
            if path_part.startswith('/'):
                file_path = path_part
            else:
                file_path = str(Path(path_part).resolve())
        else:
            file_path = db_path
        
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        logger.error(f"Failed to query SQLite: {e}")
        return []


def get_postgres_tables(db_url: str) -> List[str]:
    """Get list of all tables in PostgreSQL database."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username or 'postgres',
            password=parsed.password or '',
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema='public' 
            ORDER BY table_name
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [r[0] for r in rows]
    except ImportError:
        return ["(psycopg2 not installed)"]
    except Exception as e:
        logger.error(f"Failed to query PostgreSQL: {e}")
        return []


def list_tables() -> Dict:
    """List all tables in configured database."""
    db_url = get_database_url()
    result = {
        'database_url': mask_database_url(db_url),
        'db_type': None,
        'tables': [],
        'count': 0,
        'error': None,
    }
    
    try:
        if 'sqlite' in db_url:
            result['db_type'] = 'sqlite'
            result['tables'] = get_sqlite_tables(db_url)
        elif 'postgres' in db_url:
            result['db_type'] = 'postgresql'
            result['tables'] = get_postgres_tables(db_url)
        else:
            result['error'] = f"Unknown database type: {db_url}"
            return result
        
        result['count'] = len(result['tables'])
    except Exception as e:
        result['error'] = str(e)
    
    return result


def main():
    """List tables and print results."""
    result = list_tables()
    
    print("\n" + "="*80)
    print("DATABASE TABLE LIST")
    print("="*80 + "\n")
    
    print(f"Database URL: {result['database_url']}")
    print(f"Database Type: {result['db_type']}")
    print(f"Total Tables: {result['count']}")
    
    if result['error']:
        print(f"\nError: {result['error']}")
        return 1
    
    if result['tables']:
        print("\nTables:")
        for i, table in enumerate(result['tables'], 1):
            print(f"  {i:2d}. {table}")
    else:
        print("\nNo tables found.")
    
    # Check for critical AOL tables
    aol_tables = {'aol_control_flags', 'aol_tick_ledger', 'aol_lease', 'aol_actions', 'aol_execution_logs'}
    present = aol_tables & set(result['tables'])
    missing = aol_tables - set(result['tables'])
    
    if missing:
        print(f"\n⚠️  MISSING AOL TABLES ({len(missing)}/{len(aol_tables)}):")
        for table in sorted(missing):
            print(f"   - {table}")
    else:
        print(f"\n✓ All {len(aol_tables)} AOL tables present")
    
    print("\n" + "="*80 + "\n")
    
    return 0 if not result['error'] else 1


if __name__ == "__main__":
    sys.exit(main())
