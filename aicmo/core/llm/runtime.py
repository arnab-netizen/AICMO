"""
LLM Runtime Configuration & Graceful Degradation.

Purpose:
  Centralize LLM "enabled" checks and provide graceful degradation
  when OpenAI API key is missing or LLM is disabled.

Strategy:
  1. Implement llm_enabled() to check both API key + optional feature flag
  2. Implement require_llm() that raises clear error with setup instructions
  3. Implement safe_llm_status() for diagnostics
  4. Never import heavy LLM modules at import-time (lazy import only)

Usage:
  # Check if LLM is available
  if llm_enabled():
      # Safe to call LLM functions
      from aicmo.core.llm import generate_something
  
  # Require LLM or fail with clear message
  require_llm()  # Raises RuntimeError with setup instructions if not available
  
  # Get status for diagnostics
  status = safe_llm_status()  # Returns dict with enabled, reason, etc.
"""

import os
from typing import Dict, Optional


def llm_enabled() -> bool:
    """
    Check if LLM integration is enabled and configured.
    
    Returns True if:
      - OPENAI_API_KEY environment variable is set (non-empty)
      - AICMO_USE_LLM is not explicitly set to 0/false (optional check)
    
    Returns:
        bool: True if LLM is available and configured
    """
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    if not api_key:
        return False
    
    # Optional: Check feature flag (defaults to enabled if key exists)
    use_llm = os.getenv('AICMO_USE_LLM', '1').strip().lower()
    if use_llm in ('0', 'false', 'no'):
        return False
    
    return True


def require_llm() -> None:
    """
    Assert that LLM is enabled; raise RuntimeError with setup instructions if not.
    
    Call this at the start of any function that requires LLM.
    Do NOT import this at module level; only call at function level.
    
    Raises:
        RuntimeError: If LLM is not enabled, with clear setup instructions
        
    Example:
        def generate_campaign_title(brief):
            require_llm()  # Fail early with clear error
            # ... rest of function
    """
    if llm_enabled():
        return
    
    instructions = """
╔════════════════════════════════════════════════════════════════════╗
║  LLM Integration is Not Configured                                 ║
╚════════════════════════════════════════════════════════════════════╝

This operation requires OpenAI API access.

To enable LLM features, configure your environment:

  1. Set your API key:
     export OPENAI_API_KEY="sk-..."
  
  2. Optional: Enable LLM explicitly:
     export AICMO_USE_LLM=1
  
  3. Restart the application

Without LLM, you can still use:
  - Manual lead entry and management
  - Template-based outreach
  - Basic analytics

To obtain an API key:
  Visit: https://platform.openai.com/account/api-keys
"""
    raise RuntimeError(instructions)


def safe_llm_status() -> Dict[str, object]:
    """
    Get LLM status for diagnostics (safe to call anytime).
    
    Returns:
        Dict with keys:
          - enabled: bool (True if LLM is available)
          - has_api_key: bool (True if OPENAI_API_KEY is set)
          - feature_flag: str (AICMO_USE_LLM value, 'not set' if missing)
          - reason: str (Human-readable status/reason if disabled)
    """
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    has_key = bool(api_key)
    
    use_llm_env = os.getenv('AICMO_USE_LLM', 'not set').strip().lower()
    is_disabled = use_llm_env in ('0', 'false', 'no')
    
    enabled = has_key and not is_disabled
    
    if not has_key:
        reason = "OPENAI_API_KEY not set"
    elif is_disabled:
        reason = f"AICMO_USE_LLM={use_llm_env} (disabled)"
    else:
        reason = "LLM enabled and ready"
    
    return {
        'enabled': enabled,
        'has_api_key': has_key,
        'feature_flag': use_llm_env,
        'reason': reason,
    }


__all__ = [
    'llm_enabled',
    'require_llm',
    'safe_llm_status',
]
