"""
Thin wrapper around existing DB/session setup.

This allows new modules to import from aicmo.core without depending
directly on backend.* paths, making the code more portable.
"""

import os
import re
from typing import Dict, List, Optional

try:
    from backend.db.base import Base
    from backend.db.session import get_session
except ImportError:
    # Fallback for legacy imports
    from backend.db import Base, get_session  # type: ignore

# For convenience, create a SessionLocal-like factory
def SessionLocal():
    """Get a database session (generator wrapper for compatibility)."""
    return next(get_session())


# ═══════════════════════════════════════════════════════════════════════
# DATABASE URL VALIDATION & ASYNC/SYNC DRIVER MISMATCH DETECTION
# ═══════════════════════════════════════════════════════════════════════

def validate_database_url(url: Optional[str] = None) -> Dict:
    """
    Validate database URL for consistency and driver availability.
    
    Args:
        url: Optional DATABASE_URL override. If not provided, reads from env.
    
    Returns:
        Dict with keys:
          - valid: bool (True if no blocking issues)
          - database_url: str (masked URL or None)
          - db_type: str ('sqlite', 'postgresql', 'unknown', or None)
          - is_async: bool (True if URL specifies async driver)
          - driver: str (parsed driver name, e.g., 'asyncpg', 'psycopg2')
          - issues: List[str] (human-readable issues found)
          - warnings: List[str] (non-blocking concerns)
    """
    result = {
        'valid': True,
        'database_url': None,
        'db_type': None,
        'is_async': False,
        'driver': None,
        'issues': [],
        'warnings': [],
    }
    
    # Get database URL
    db_url = url or os.getenv('DATABASE_URL', 'sqlite:///local.db')
    result['database_url'] = mask_url(db_url)
    
    if not db_url:
        result['issues'].append("DATABASE_URL is empty")
        result['valid'] = False
        return result
    
    # Parse URL scheme
    # Format: driver+dialect://user:pass@host:port/dbname
    match = re.match(r'(\w+)\+?(\w*)?://', db_url)
    if not match:
        result['issues'].append(f"Invalid database URL format: {db_url}")
        result['valid'] = False
        return result
    
    dialect = match.group(1)
    driver_name = match.group(2) or dialect
    
    # Determine database type
    if 'sqlite' in dialect:
        result['db_type'] = 'sqlite'
        result['is_async'] = False
    elif 'postgres' in dialect:
        result['db_type'] = 'postgresql'
        result['is_async'] = 'asyncpg' in driver_name
        result['driver'] = driver_name or 'psycopg2'  # psycopg2 is default
    else:
        result['db_type'] = dialect
        result['driver'] = driver_name
    
    # Validate PostgreSQL async driver
    if result['db_type'] == 'postgresql':
        if result['is_async']:
            # Using async - check if asyncpg is installed
            if not _is_module_installed('asyncpg'):
                result['issues'].append(
                    f"URL specifies asyncpg driver but asyncpg is not installed. "
                    f"Install: pip install asyncpg"
                )
                result['valid'] = False
        else:
            # Using sync (psycopg2) - check if it's installed
            if not _is_module_installed('psycopg2'):
                result['warnings'].append(
                    f"PostgreSQL driver psycopg2 not found. "
                    f"Install: pip install psycopg2-binary"
                )
    
    # Validate SQLite path if local file
    if result['db_type'] == 'sqlite':
        # Extract file path from url
        path_match = re.match(r'sqlite:///(.+)', db_url)
        if path_match:
            db_path = path_match.group(1)
            if db_path and not db_path.startswith('/'):
                # Relative path - warn about persistence
                result['warnings'].append(
                    f"SQLite using relative path: {db_path}. "
                    f"Data may not persist across directory changes or deployments."
                )
    
    return result


def mask_url(url: str) -> str:
    """Mask credentials in database URL for safe display."""
    if '://' not in url:
        return url
    
    scheme, rest = url.split('://', 1)
    if '@' in rest:
        creds, host_part = rest.rsplit('@', 1)
        user = creds.split(':', 1)[0] if ':' in creds else creds
        return f"{scheme}://{user}:***@{host_part}"
    return url


def _is_module_installed(module_name: str) -> bool:
    """Check if a Python module is installed without importing it."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


__all__ = ["SessionLocal", "Base", "get_session", "validate_database_url", "mask_url"]
