"""
Self-Test Engine Security & Privacy Checkers

Pattern-based scanning for:
- Secret-like patterns (API keys, tokens)
- Environment variable placeholders
- Prompt injection markers
"""

import re
from dataclasses import dataclass, field
from typing import List
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PATTERNS FOR SECURITY SCANNING
# ============================================================================

# API key-like patterns: common prefixes and long random strings
SECRET_PATTERNS = [
    # Common API key prefixes (OpenAI, Anthropic, Hugging Face, etc.)
    r'\bsk-[A-Za-z0-9]{20,}',  # OpenAI-style: sk-*
    r'\bkey_[A-Za-z0-9]{20,}',  # Generic: key_*
    r'\btoken_[A-Za-z0-9]{20,}',  # Generic: token_*
    r'\bsecret[_-]?[A-Za-z0-9]{20,}',  # Generic: secret*
    r'\bauth[_-]?[A-Za-z0-9]{20,}',  # Generic: auth*
    r'\bpat_[A-Za-z0-9]{20,}',  # Hugging Face PAT
    r'\bapid_[A-Za-z0-9]{20,}',  # Various API prefixes
    r'\b[A-Z0-9]{32,}\b',  # Very long hex-like strings (32+ chars)
]

# Environment variable placeholders
ENV_PATTERNS = [
    r'\$\{[A-Z_][A-Z0-9_]*\}',  # ${ENV_VAR}
    r'\{\{[A-Z_][A-Z0-9_]*\}\}',  # {{ENV_VAR}}
    r'\$[A-Z_][A-Z0-9_]*(?=\s|$|[,\.\;:])',  # $ENV_VAR (with word boundary)
]

# Prompt injection markers
PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+previous\s+instructions',
    r'disregard\s+all\s+previous\s+instructions',
    r'as\s+an\s+ai\s+language\s+model',
    r'as\s+a\s+language\s+model',
    r'as\s+an\s+ai\s+assistant',
    r'forget\s+(?:the|all)\s+previous',
    r'pretend\s+(?:you\s+are|that\s+you)',
    r'act\s+as\s+if\s+you\s+are',
    r'role\s+play(?:ing)?',
    r'(?:new|reset)\s+(?:instructions|prompt|system)',
    r'(?:follow|use)\s+(?:the\s+)?following\s+instructions',
    r'system\s+prompt',
    r'jailbreak',
    r'break\s+out\s+of\s+your\s+constraints',
]

# Compile all patterns for efficiency
COMPILED_SECRET_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SECRET_PATTERNS]
COMPILED_ENV_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ENV_PATTERNS]
COMPILED_INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS]


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SecurityScanResult:
    """Result of security/privacy scan on text outputs."""
    
    has_secret_like_patterns: bool = False
    """Whether any secret-like patterns (API keys, tokens) were detected."""
    
    has_env_like_patterns: bool = False
    """Whether any environment variable placeholders were detected."""
    
    has_prompt_injection_markers: bool = False
    """Whether any prompt injection markers were detected."""
    
    suspicious_snippets: List[str] = field(default_factory=list)
    """Sample suspicious text snippets found (truncated for privacy)."""


# ============================================================================
# SECURITY SCANNING FUNCTIONS
# ============================================================================

def _extract_context_snippet(text: str, match_start: int, match_end: int, context_chars: int = 50) -> str:
    """
    Extract a snippet around a match for reporting.
    
    Args:
        text: Full text
        match_start: Start position of match
        match_end: End position of match
        context_chars: Characters to include before/after match
    
    Returns:
        Truncated snippet with the match highlighted
    """
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)
    
    snippet = text[start:end]
    
    # Truncate if needed
    if len(snippet) > 100:
        snippet = snippet[:100] + "..."
    
    return snippet


def scan_security(texts: List[str]) -> SecurityScanResult:
    """
    Scan texts for security/privacy issues.
    
    Pattern-based checks only - no ML, no heuristics. Only flags what we actually scan for:
    - API key-like patterns
    - Environment variable placeholders
    - Prompt injection markers
    
    Args:
        texts: List of text strings to scan
    
    Returns:
        SecurityScanResult with findings
    """
    result = SecurityScanResult()
    snippets_set = set()  # Use set to avoid duplicates
    
    if not texts:
        return result
    
    # Combine all texts for scanning
    combined_text = "\n".join(texts)
    
    # Check for secret-like patterns
    for pattern in COMPILED_SECRET_PATTERNS:
        matches = pattern.finditer(combined_text)
        for match in matches:
            result.has_secret_like_patterns = True
            snippet = _extract_context_snippet(combined_text, match.start(), match.end())
            snippets_set.add(snippet)
            logger.debug(f"Found potential secret pattern: {match.group()[:20]}...")
    
    # Check for environment variable placeholders
    for pattern in COMPILED_ENV_PATTERNS:
        matches = pattern.finditer(combined_text)
        for match in matches:
            result.has_env_like_patterns = True
            snippet = _extract_context_snippet(combined_text, match.start(), match.end())
            snippets_set.add(snippet)
            logger.debug(f"Found potential env placeholder: {match.group()}")
    
    # Check for prompt injection markers
    for pattern in COMPILED_INJECTION_PATTERNS:
        matches = pattern.finditer(combined_text)
        for match in matches:
            result.has_prompt_injection_markers = True
            snippet = _extract_context_snippet(combined_text, match.start(), match.end())
            snippets_set.add(snippet)
            logger.debug(f"Found potential prompt injection marker: {match.group()}")
    
    # Convert set to sorted list and limit to first 5 snippets
    result.suspicious_snippets = sorted(list(snippets_set))[:5]
    
    return result
