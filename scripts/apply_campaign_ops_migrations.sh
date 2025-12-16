#!/bin/bash
################################################################################
# Apply Campaign Ops Database Migrations
#
# This script:
# 1. Verifies DATABASE_URL is set
# 2. Displays sanitized DB identity
# 3. Applies all pending Alembic migrations (including Campaign Ops)
# 4. Verifies Campaign Ops tables exist
# 5. Exits with clear error on failure
#
# Safe for Render, CI/CD, and non-interactive deployment.
# No manual steps required.
################################################################################

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==============================================================================="
echo "Campaign Ops Database Migration Script"
echo "==============================================================================="
echo ""

# ============================================================================
# Step 1: Verify DATABASE_URL is set
# ============================================================================

if [ -z "$DATABASE_URL" ] && [ -z "$DATABASE_URL_SYNC" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL or DATABASE_URL_SYNC environment variable not set${NC}"
    echo ""
    echo "Set one of the following:"
    echo "  export DATABASE_URL=postgresql://user:pass@host:5432/dbname"
    echo "  export DATABASE_URL_SYNC=postgresql+psycopg2://user:pass@host:5432/dbname"
    exit 1
fi

# Use SYNC URL if available (works with alembic), fallback to async URL
if [ -n "$DATABASE_URL_SYNC" ]; then
    DB_URL="$DATABASE_URL_SYNC"
else
    # Convert async URL to sync for alembic
    DB_URL="${DATABASE_URL/+asyncpg/+psycopg2}"
fi

echo "Database: $DB_URL" | sed 's/:[^@]*@/@/g'
echo ""

# ============================================================================
# Step 2: Parse DB identity (sanitized - no password)
# ============================================================================

# Extract connection components (basic parsing for display only)
PARSED_URL=$(echo "$DB_URL" | sed 's#postgresql[+a-z0-9]*://##')
DB_USER=$(echo "$PARSED_URL" | cut -d: -f1)
DB_HOST=$(echo "$PARSED_URL" | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo "$PARSED_URL" | cut -d@ -f2 | cut -d: -f2 | cut -d/ -f1)
DB_NAME=$(echo "$PARSED_URL" | cut -d/ -f2)

echo "DB Identity (sanitized):"
echo "  Host: $DB_HOST"
echo "  Port: ${DB_PORT:-5432}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# ============================================================================
# Step 3: Apply migrations
# ============================================================================

echo "Applying Alembic migrations..."
echo ""

if ! python -m alembic upgrade head 2>&1 | tee /tmp/alembic_upgrade.log; then
    echo ""
    echo -e "${RED}❌ Migration failed. Check log above.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Migrations applied successfully${NC}"
echo ""

# ============================================================================
# Step 4: Verify Campaign Ops tables exist
# ============================================================================

echo "Verifying Campaign Ops tables..."
python3 << 'VERIFY_SCRIPT'
import os
import sys
from sqlalchemy import create_engine, inspect

# Use sync URL for verification
db_url = os.getenv('DATABASE_URL_SYNC')
if not db_url:
    db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '+psycopg2')

if not db_url:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

try:
    engine = create_engine(db_url)
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    required_tables = [
        'campaign_ops_campaigns',
        'campaign_ops_plans',
        'campaign_ops_calendar_items',
        'campaign_ops_operator_tasks',
        'campaign_ops_metric_entries',
        'campaign_ops_audit_log',
    ]
    
    found_tables = [t for t in required_tables if t in all_tables]
    missing_tables = [t for t in required_tables if t not in all_tables]
    
    print(f"Campaign Ops tables: {len(found_tables)}/{len(required_tables)}")
    
    for table in found_tables:
        print(f"  ✅ {table}")
    
    for table in missing_tables:
        print(f"  ❌ {table}")
    
    if missing_tables:
        print("\n❌ Some Campaign Ops tables are missing!")
        sys.exit(1)
    
    print("\n✅ All Campaign Ops tables exist!")
    sys.exit(0)

except Exception as e:
    print(f"❌ Verification error: {e}")
    sys.exit(1)

VERIFY_SCRIPT

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "==============================================================================="
echo "✅ SUCCESS: Campaign Ops database is ready!"
echo "==============================================================================="
exit 0
