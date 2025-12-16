#!/usr/bin/env python3
"""
Verify Campaign Ops Tables Exist

This script:
- Connects to DATABASE_URL
- Checks for all 6 required Campaign Ops tables
- Returns exit code 0 only if all tables exist
- Returns exit code 1 and lists missing tables if any are absent
- Prints sanitized DB identity for debugging

Usage:
  python audit_artifacts/campaign_ops_fix/verify_campaign_ops_tables.py

Returns:
  0 if all 6 tables exist
  1 if any are missing or connection fails
"""

import os
import sys
from sqlalchemy import create_engine, inspect

def main():
    """Verify Campaign Ops tables exist in the database."""
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL_SYNC')
    if not db_url:
        db_url = os.getenv('DATABASE_URL', '')
        # Convert async to sync if needed
        if '+asyncpg' in db_url:
            db_url = db_url.replace('+asyncpg', '+psycopg2')
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL or DATABASE_URL_SYNC not set")
        return 1
    
    # Display sanitized DB identity
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        print("=" * 70)
        print("Campaign Ops Database Table Verification")
        print("=" * 70)
        print(f"\nDatabase Identity (sanitized):")
        print(f"  Scheme: {parsed.scheme}")
        print(f"  Host: {parsed.hostname}")
        print(f"  Port: {parsed.port or 5432}")
        print(f"  Database: {parsed.path.lstrip('/')}")
        print(f"  User: {parsed.username}")
        print()
    except Exception as e:
        print(f"⚠️  Could not parse DB URL: {e}")
    
    # Connect to database
    try:
        engine = create_engine(db_url)
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database")
        print(f"   {e}")
        return 1
    
    # Define required tables
    required_tables = [
        'campaign_ops_campaigns',
        'campaign_ops_plans',
        'campaign_ops_calendar_items',
        'campaign_ops_operator_tasks',
        'campaign_ops_metric_entries',
        'campaign_ops_audit_log',
    ]
    
    # Check for each table
    found_tables = []
    missing_tables = []
    
    for table in required_tables:
        if table in all_tables:
            found_tables.append(table)
        else:
            missing_tables.append(table)
    
    # Print results
    print(f"Campaign Ops Tables: {len(found_tables)}/{len(required_tables)}")
    print()
    
    if found_tables:
        print("✅ Found:")
        for table in found_tables:
            print(f"   - {table}")
    
    if missing_tables:
        print()
        print("❌ Missing:")
        for table in missing_tables:
            print(f"   - {table}")
        print()
        print("To fix, run:")
        print("  cd /workspaces/AICMO")
        print("  bash scripts/apply_campaign_ops_migrations.sh")
        return 1
    
    print()
    print("=" * 70)
    print("✅ SUCCESS: All Campaign Ops tables exist!")
    print("=" * 70)
    return 0

if __name__ == '__main__':
    sys.exit(main())
