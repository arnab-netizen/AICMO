"""
AICMO V2 Shared Utilities

Provides:
- Safe session wrapping (fix #C1)
- Backend HTTP helpers (fix #D)
- DB diagnostics helpers (fix #C3)
- Consistent error handling and UI components
"""

import os
import streamlit as st
import httpx
from typing import Optional, Dict, Any
from contextlib import contextmanager

# ===================================================================
# BUILD MARKER (copied from operator_v2.py for reference)
# ===================================================================
DASHBOARD_BUILD = os.getenv("DASHBOARD_BUILD", "OPERATOR_V2_DEV")

# ===================================================================
# SAFE SESSION WRAPPER (Fix #C1: _GeneratorContextManager issue)
# ===================================================================

@contextmanager
def safe_session(get_session_fn):
    """
    Wraps get_session() to ensure proper context manager usage.
    
    Usage:
        from backend.db.session import get_session
        from aicmo.ui_v2.shared import safe_session
        
        with safe_session(get_session) as s:
            result = s.query(...).all()
    """
    try:
        with get_session_fn() as session:
            yield session
    except Exception as e:
        st.error(f"Database session error: {str(e)}")
        raise


# ===================================================================
# BACKEND HTTP HELPERS (Fix #D: Prefer backend over direct DB)
# ===================================================================

def backend_base_url() -> str:
    """
    Resolve backend URL from environment.
    Prefers AICMO_BACKEND_URL if set, else falls back to BACKEND_URL.
    Returns None if neither is set (backend unavailable).
    """
    base_url = os.getenv("AICMO_BACKEND_URL") or os.getenv("BACKEND_URL")
    return base_url


def http_get_json(path: str, timeout: int = 5) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Make HTTP GET request to backend.
    
    Returns:
        (success: bool, data: dict or None, error_msg: str or None)
    """
    base_url = backend_base_url()
    if not base_url:
        return False, None, "Backend URL not configured"
    
    url = f"{base_url}{path}" if not path.startswith("http") else path
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        if response.status_code == 200:
            return True, response.json(), None
        else:
            return False, None, f"Backend returned {response.status_code}: {response.text[:200]}"
    except httpx.TimeoutException:
        return False, None, f"Request timeout after {timeout}s"
    except httpx.ConnectError as e:
        return False, None, f"Cannot connect to backend: {str(e)[:100]}"
    except Exception as e:
        return False, None, f"HTTP error: {str(e)[:100]}"


def http_post_json(path: str, payload: Dict[str, Any], timeout: int = 5) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Make HTTP POST request to backend.
    
    Returns:
        (success: bool, data: dict or None, error_msg: str or None)
    """
    base_url = backend_base_url()
    if not base_url:
        return False, None, "Backend URL not configured"
    
    url = f"{base_url}{path}" if not path.startswith("http") else path
    try:
        response = httpx.post(url, json=payload, timeout=timeout, follow_redirects=True)
        if response.status_code in [200, 201]:
            return True, response.json(), None
        else:
            return False, None, f"Backend returned {response.status_code}: {response.text[:200]}"
    except httpx.TimeoutException:
        return False, None, f"Request timeout after {timeout}s"
    except httpx.ConnectError as e:
        return False, None, f"Cannot connect to backend: {str(e)[:100]}"
    except Exception as e:
        return False, None, f"HTTP error: {str(e)[:100]}"


# ===================================================================
# DB DIAGNOSTICS HELPERS (Fix #C3: Campaign Ops DB connection)
# ===================================================================

def check_db_env_vars() -> Dict[str, Any]:
    """
    Check if DB environment variables are properly configured.
    
    Returns:
        {
            'db_url_configured': bool,
            'db_url_valid': bool,
            'db_url': str (masked),
            'issues': [str],
            'recommendations': [str]
        }
    """
    db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
    
    result = {
        'db_url_configured': bool(db_url),
        'db_url_valid': False,
        'db_url': '(not set)',
        'issues': [],
        'recommendations': []
    }
    
    if not db_url:
        result['issues'].append("No DB_URL or DATABASE_URL environment variable set")
        result['recommendations'].append("Set DB_URL=postgresql://user:pass@host/dbname")
        return result
    
    # Mask password
    masked_url = db_url
    if '://' in db_url:
        scheme, rest = db_url.split('://', 1)
        if '@' in rest:
            creds, host = rest.split('@', 1)
            masked_url = f"{scheme}://***:***@{host}"
    result['db_url'] = masked_url
    
    # Check for placeholder values
    placeholder_patterns = [
        ('postgresql+psycopg2://postgres/appdb', 'Placeholder DB URL'),
        ('sqlite:///:memory:', 'In-memory DB (development only)'),
        ('postgresql://localhost', 'Unprotected local DB'),
    ]
    
    for pattern, desc in placeholder_patterns:
        if pattern in db_url or db_url.startswith(pattern):
            result['issues'].append(f"Detected {desc}: {pattern}")
            result['recommendations'].append("Update to production DB URL")
    
    # Check if it looks valid
    if db_url.startswith(('postgresql://', 'postgres://', 'sqlite://', 'mysql://')):
        result['db_url_valid'] = True
    else:
        result['issues'].append("DB URL scheme not recognized")
        result['recommendations'].append("Use postgresql://, postgres://, sqlite://, or mysql://")
    
    # SSL check
    if 'postgresql' in db_url and 'sslmode' not in db_url:
        result['recommendations'].append("Consider adding ?sslmode=require for Render/Neon")
    
    return result


def check_db_connectivity(get_session_fn) -> Dict[str, Any]:
    """
    Attempt a simple DB connection test.
    
    Returns:
        {
            'connected': bool,
            'db_type': str,
            'db_name': str or None,
            'error': str or None,
            'ssl_info': str or None
        }
    """
    result = {
        'connected': False,
        'db_type': None,
        'db_name': None,
        'error': None,
        'ssl_info': None
    }
    
    try:
        # Try to get a session
        with get_session_fn() as session:
            # Execute a simple query
            query_result = session.execute("SELECT 1")
            _ = query_result.fetchone()
            result['connected'] = True
            
            # Try to get DB info
            db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL", "unknown")
            if 'postgresql' in db_url:
                result['db_type'] = 'PostgreSQL'
                try:
                    db_info = session.execute("SELECT current_database()")
                    db_name = db_info.fetchone()[0]
                    result['db_name'] = db_name
                except:
                    pass
            elif 'mysql' in db_url:
                result['db_type'] = 'MySQL'
            elif 'sqlite' in db_url:
                result['db_type'] = 'SQLite'
    
    except Exception as e:
        result['error'] = str(e)[:200]
        
        # Check for SSL errors
        if 'SSL' in str(e) or 'ssl' in str(e).lower():
            result['ssl_info'] = "SSL error detected. Try adding ?sslmode=require to DB_URL"
    
    return result


# ===================================================================
# UI COMPONENTS FOR CONSISTENT DISPLAY
# ===================================================================

def render_status_banner(tab_name: str, backend_status: Optional[str], db_status: Optional[str]):
    """
    Render a status banner showing backend and DB connectivity.
    
    Args:
        tab_name: Name of the tab (for logging)
        backend_status: "OK" or error message
        db_status: "OK" or error message
    """
    col1, col2 = st.columns(2)
    
    with col1:
        if backend_status == "OK":
            st.success("✅ Backend: OK")
        else:
            st.error(f"❌ Backend: {backend_status or 'Not configured'}")
    
    with col2:
        if db_status == "OK":
            st.success("✅ Database: OK")
        else:
            st.error(f"❌ Database: {db_status or 'Not configured'}")


def render_diagnostics_panel():
    """
    Render a comprehensive diagnostics panel showing environment and connectivity.
    Called from System/Diagnostics tab.
    """
    st.subheader("🔍 System Diagnostics")
    
    # Environment section
    with st.expander("📋 Environment Variables", expanded=True):
        env_info = {
            'BUILD': DASHBOARD_BUILD,
            'BACKEND_URL': os.getenv('AICMO_BACKEND_URL') or os.getenv('BACKEND_URL') or '(not set)',
            'DB_URL': (os.getenv('DB_URL') or os.getenv('DATABASE_URL') or '(not set)')[:50] + '...',
            'STREAMLIT_SECRETS': 'Configured' if hasattr(st, 'secrets') else '(not available)',
        }
        
        for key, value in env_info.items():
            st.write(f"**{key}**: `{value}`")
    
    # DB configuration check
    with st.expander("🗄️  Database Configuration", expanded=False):
        try:
            from backend.db.session import get_session
            
            env_check = check_db_env_vars()
            st.write("**Configuration Status:**")
            if env_check['issues']:
                for issue in env_check['issues']:
                    st.error(f"⚠️ {issue}")
            else:
                st.success("✅ Database configuration looks valid")
            
            if env_check['recommendations']:
                st.info("**Recommendations:**\n" + "\n".join(f"- {r}" for r in env_check['recommendations']))
            
            # Try connectivity test
            st.write("**Connectivity Test:**")
            conn_check = check_db_connectivity(get_session)
            if conn_check['connected']:
                st.success(f"✅ Connected to {conn_check['db_type']}")
                if conn_check['db_name']:
                    st.write(f"Database: `{conn_check['db_name']}`")
            else:
                st.error(f"❌ Connection failed: {conn_check['error']}")
        
        except ImportError:
            st.warning("Cannot import backend DB session")
    
    # Backend connectivity check
    with st.expander("🌐 Backend Connectivity", expanded=False):
        base_url = backend_base_url()
        if base_url:
            st.write(f"**Backend URL**: `{base_url}`")
            if st.button("Test Backend Connection"):
                success, data, error = http_get_json("/health", timeout=3)
                if success:
                    st.success("✅ Backend is reachable")
                    st.json(data)
                else:
                    st.error(f"❌ {error}")
        else:
            st.warning("⚠️ Backend URL not configured")
