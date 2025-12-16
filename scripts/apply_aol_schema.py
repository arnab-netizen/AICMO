#!/usr/bin/env python3
"""
Apply AOL schema to configured database.

Purpose:
  Create AOL tables if they don't exist. Idempotent and safe.
  Works with PostgreSQL or SQLite.

Usage:
  python scripts/apply_aol_schema.py

Environment:
  DATABASE_URL or DB_URL: connection string (uses standard priority)
  
Returns:
  0 if successful, 1 if error
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List

# Add workspace to path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from aicmo.orchestration.models import Base

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Get configured database URL (respecting same priority as backend/db/session.py)."""
    return os.getenv("DB_URL") or os.getenv("DATABASE_URL") or "sqlite+pysqlite:///:memory:"


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


def apply_aol_schema() -> Dict:
    """Apply AOL schema to database (idempotent)."""
    result = {
        'success': False,
        'database_url': None,
        'db_type': None,
        'tables_before': [],
        'tables_created': [],
        'error': None,
    }
    
    db_url = get_database_url()
    result['database_url'] = mask_database_url(db_url)
    
    try:
        # Determine DB type
        if 'sqlite' in db_url:
            result['db_type'] = 'sqlite'
            connect_args = {"check_same_thread": False}
        elif 'postgres' in db_url:
            result['db_type'] = 'postgresql'
            connect_args = {}
        else:
            result['db_type'] = 'unknown'
            connect_args = {}
        
        # Create engine
        engine = create_engine(db_url, connect_args=connect_args, future=True)
        
        # Get tables before
        inspector = inspect(engine)
        tables_before = inspector.get_table_names()
        result['tables_before'] = tables_before
        
        logger.info(f"Database: {result['database_url']}")
        logger.info(f"Type: {result['db_type']}")
        logger.info(f"Tables before: {len(tables_before)}")
        
        # Create AOL tables
        logger.info("Creating AOL tables...")
        Base.metadata.create_all(engine)
        
        # Get tables after
        inspector = inspect(engine)
        tables_after = inspector.get_table_names()
        
        # Find newly created tables
        aol_tables = {'aol_control_flags', 'aol_tick_ledger', 'aol_lease', 'aol_actions', 'aol_execution_logs'}
        created = aol_tables & set(tables_after)
        result['tables_created'] = list(created)
        
        logger.info(f"AOL tables created: {len(created)}/{len(aol_tables)}")
        
        if len(created) == len(aol_tables):
            result['success'] = True
            logger.info("✓ All AOL tables successfully created")
        else:
            missing = aol_tables - set(tables_after)
            result['error'] = f"Some tables still missing: {missing}"
            logger.error(result['error'])
        
        engine.dispose()
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Failed to apply schema: {e}")
    
    return result


def main():
    """Apply schema and print results."""
    print("\n" + "="*80)
    print("APPLY AOL SCHEMA")
    print("="*80 + "\n")
    
    result = apply_aol_schema()
    
    if result['error']:
        print(f"\n❌ Error: {result['error']}")
        return 1
    
    if result['success']:
        print(f"\n✓ Schema applied successfully")
        print(f"  Tables created: {', '.join(sorted(result['tables_created']))}")
        print("\n" + "="*80 + "\n")
        return 0
    else:
        print(f"\n❌ Schema not fully created")
        return 1


if __name__ == "__main__":
    sys.exit(main())
