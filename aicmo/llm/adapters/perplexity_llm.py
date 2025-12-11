"""
Perplexity LLM adapter - Web search + reasoning LLM provider.

Supports multiple Sonar variants:
- sonar: Fast web search + generation
- sonar-reasoning: Slower, deeper reasoning with web search
- sonar-deep-research: Exhaustive research (requires feature flag, API limit enforcement)

Production use: Requires PERPLEXITY_API_KEY environment variable.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PerplexityHealth(Enum):
    """Health status of Perplexity provider."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class PerplexityProviderStatus:
    """Health metrics for Perplexity provider."""
    health: PerplexityHealth = PerplexityHealth.UNKNOWN
    error_message: Optional[str] = None
    last_check_timestamp: Optional[float] = None


class PerplexityLLMAdapter:
    """
    Perplexity LLM adapter with web search capabilities.
    
    Supports dry_run mode (returns stub responses).
    Production mode requires PERPLEXITY_API_KEY.
    
    Models:
    - sonar: Standard (fast)
    - sonar-reasoning: Extended thinking (slower, deeper)
    - sonar-deep-research: Exhaustive (requires ENABLE_PERPLEXITY_DEEP_RESEARCH flag + API limit enforcement)
    """
    
    def __init__(self, api_key: Optional[str] = None, dry_run: bool = True, model: str = "sonar"):
        """
        Initialize Perplexity LLM adapter.
        
        Args:
            api_key: Perplexity API key (optional, uses env var if not provided)
            dry_run: If True, returns stub responses without calling API
            model: Which Sonar variant to use (sonar, sonar-reasoning, sonar-deep-research)
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.dry_run = dry_run
        self.model = model
        self.name = "perplexity_llm"
        self.kind = "llm"
        self._status = PerplexityProviderStatus()
    
    def get_name(self) -> str:
        """Get provider name for logging."""
        return f"{self.name}[{self.model}]"
    
    def check_health(self, force: bool = False) -> PerplexityProviderStatus:
        """
        Check health status of Perplexity provider.
        
        Also checks if sonar-deep-research is allowed (if model specifies it).
        
        Args:
            force: Force re-check (currently unused)
        
        Returns:
            PerplexityProviderStatus with health and error details
        """
        if self.dry_run:
            self._status.health = PerplexityHealth.HEALTHY
            self._status.error_message = None
            return self._status
        
        if not self.api_key:
            self._status.health = PerplexityHealth.UNHEALTHY
            self._status.error_message = "PERPLEXITY_API_KEY not configured"
            return self._status
        
        # Check if deep-research is allowed
        if self.model == "sonar-deep-research":
            enabled = os.getenv("ENABLE_PERPLEXITY_DEEP_RESEARCH", "false").lower() == "true"
            if not enabled:
                self._status.health = PerplexityHealth.UNHEALTHY
                self._status.error_message = "sonar-deep-research requires ENABLE_PERPLEXITY_DEEP_RESEARCH=true"
                return self._status
        
        self._status.health = PerplexityHealth.HEALTHY
        self._status.error_message = None
        return self._status
    
    def generate(self, prompt: str, include_search: bool = True, **kwargs) -> str:
        """
        Generate text completion from prompt (with optional web search).
        
        Args:
            prompt: Input prompt text
            include_search: If True (default), include web search in response
            **kwargs: Additional options (temperature, max_tokens, etc)
        
        Returns:
            Generated text string
        """
        if self.dry_run:
            logger.info(f"[DRY_RUN] Perplexity ({self.model}) generating from prompt: {prompt[:50]}...")
            search_note = " (with search)" if include_search else ""
            return f"[DRY_RUN: Perplexity{search_note} response to: {prompt[:30]}...]"
        
        if not self.api_key:
            logger.warning("Perplexity API key not configured, returning stub")
            return f"[STUB: Perplexity response to: {prompt[:30]}...]"
        
        # TODO: Implement real Perplexity API call
        logger.warning("Perplexity.generate() not yet fully implemented, returning stub")
        return f"[STUB: Perplexity response to: {prompt[:30]}...]"
    
    def generate_structured(self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate structured output (JSON) from prompt.
        
        Args:
            prompt: Input prompt text
            schema: JSON schema for structured output (optional)
            **kwargs: Additional options
        
        Returns:
            Dictionary with structured response
        """
        return {
            "status": "stub",
            "message": "Perplexity structured output not yet implemented",
        }
