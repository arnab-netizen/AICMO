"""
Database Diagnostics Helper

Provides database identity and connection info for debugging.

Used by:
- Streamlit operator dashboard (diagnostic display)
- AOL worker startup (diagnostic log)
- Testing and troubleshooting
"""

import os
from typing import Dict, Optional
from urllib.parse import urlparse


def get_db_identity() -> Dict[str, Optional[str]]:
    """
    Get sanitized database connection identity.
    
    Returns dict with:
    - scheme (e.g., 'postgresql')
    - host
    - port
    - database
    - user
    - (password is NEVER included)
    
    Handles both sync and async URLs.
    
    Returns:
        Dict with DB identity components
        Empty dict if DATABASE_URL not found
    """
    # Get database URL
    db_url = os.getenv('DATABASE_URL_SYNC')
    if not db_url:
        db_url = os.getenv('DATABASE_URL', '')
    
    if not db_url:
        return {}
    
    # Convert async to sync URL for display consistency
    if '+asyncpg' in db_url:
        db_url = db_url.replace('+asyncpg', '+psycopg2')
    
    try:
        parsed = urlparse(db_url)
        return {
            'scheme': parsed.scheme,
            'host': parsed.hostname,
            'port': str(parsed.port) if parsed.port else '5432',
            'database': parsed.path.lstrip('/') if parsed.path else '',
            'user': parsed.username,
        }
    except Exception:
        return {}


def format_db_identity(include_scheme: bool = True) -> str:
    """
    Format database identity as human-readable string.
    
    Examples:
        "postgresql@localhost:5432/aicmo (user: postgres)"
        "localhost:5432/aicmo (user: postgres)"
    
    Args:
        include_scheme: Whether to include postgresql:// prefix
    
    Returns:
        Formatted string or empty if DB not configured
    """
    identity = get_db_identity()
    
    if not identity:
        return "(database not configured)"
    
    parts = []
    
    if include_scheme and identity.get('scheme'):
        parts.append(f"{identity['scheme']}://")
    
    if identity.get('host'):
        parts.append(identity['host'])
    
    if identity.get('port') and identity.get('port') != '5432':
        parts[-1] = f"{parts[-1]}:{identity['port']}"
    elif identity.get('port') == '5432':
        # Don't display default port unless explicitly needed
        pass
    
    if identity.get('database'):
        parts.append(f"/{identity['database']}")
    
    result = ''.join(parts)
    
    if identity.get('user'):
        result += f" (user: {identity['user']})"
    
    return result


if __name__ == '__main__':
    # Quick test
    print("DB Identity:", format_db_identity())
    print("Full identity:", get_db_identity())
