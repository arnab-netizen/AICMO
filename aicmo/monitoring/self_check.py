"""
SelfCheckService: Automated health checks for provider chains.

Performs regular health checks on all registered providers and updates the registry
with results and recommendations. Enables automatic detection and recovery from
provider failures.

Coordinated with:
- ProviderChain: Provider health tracking
- SelfCheckRegistry: Results storage and recommendation generation
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from .registry import (
    get_registry,
    HealthCheckResult,
    ProviderRecommendation,
)

logger = logging.getLogger(__name__)


class SelfCheckService:
    """
    Automated self-healing service for provider chains.
    
    Responsibilities:
    1. Run health checks on configured providers
    2. Record results in SelfCheckRegistry
    3. Generate operator recommendations for unhealthy providers
    4. Support on-demand and scheduled checking
    """
    
    def __init__(self):
        """Initialize self-check service."""
        self.registry = get_registry()
        self._is_running = False
        self._check_task = None
    
    async def run_full_check(
        self,
        provider_chains: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run full health check on all provider chains.
        
        Args:
            provider_chains: Dict of capability -> ProviderChain (auto-loads if None)
            
        Returns:
            Dict with check results and recommendations
        """
        logger.info("Starting full health check on all providers")
        start_time = datetime.now()
        
        # Import here to avoid circular imports
        from ..gateways.provider_chain import get_all_provider_chains
        
        if provider_chains is None:
            provider_chains = get_all_provider_chains()
        
        total_checks = 0
        successful_checks = 0
        
        # Check each capability's provider chain
        for capability_name, chain in provider_chains.items():
            if chain is None or not hasattr(chain, 'providers'):
                continue
            
            logger.info(f"Checking {capability_name} ({len(chain.providers)} providers)")
            
            # Check each provider in the chain
            for wrapper in chain.providers:
                total_checks += 1
                check_start = datetime.now()
                
                try:
                    # Try a validation call (provider-specific)
                    success = await self._validate_provider(wrapper)
                    latency_ms = (datetime.now() - check_start).total_seconds() * 1000
                    
                    # Record check result
                    result = HealthCheckResult(
                        provider_name=wrapper.provider_name,
                        capability=capability_name,
                        timestamp=datetime.now(),
                        success=success,
                        latency_ms=latency_ms,
                    )
                    self.registry.record_health_check(result)
                    
                    if success:
                        successful_checks += 1
                        logger.info(
                            f"✓ {capability_name}/{wrapper.provider_name} "
                            f"health check passed ({latency_ms:.1f}ms)"
                        )
                    else:
                        logger.warning(
                            f"✗ {capability_name}/{wrapper.provider_name} "
                            f"health check failed"
                        )
                        
                        # Generate recommendation
                        rec = self._generate_recommendation(
                            wrapper.provider_name,
                            wrapper.status.health.value,
                            "Health check failed",
                        )
                        self.registry.record_recommendation(rec)
                
                except Exception as e:
                    logger.error(
                        f"✗ {capability_name}/{wrapper.provider_name} "
                        f"health check error: {e}"
                    )
                    
                    result = HealthCheckResult(
                        provider_name=wrapper.provider_name,
                        capability=capability_name,
                        timestamp=datetime.now(),
                        success=False,
                        error_message=str(e),
                    )
                    self.registry.record_health_check(result)
                    
                    # Generate recommendation
                    rec = self._generate_recommendation(
                        wrapper.provider_name,
                        "unhealthy",
                        f"Exception during check: {type(e).__name__}",
                    )
                    self.registry.record_recommendation(rec)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 0
        
        logger.info(
            f"✓ Full health check complete: {successful_checks}/{total_checks} "
            f"passed ({success_rate:.1f}%) in {elapsed:.1f}s"
        )
        
        return self.registry.get_status_report()
    
    async def _validate_provider(self, wrapper) -> bool:
        """
        Validate a provider's health.
        
        Tries to call validate_credentials or equivalent method.
        
        Args:
            wrapper: ProviderWrapper instance
            
        Returns:
            True if provider validates, False otherwise
        """
        try:
            provider = wrapper.provider
            
            # Try validate_credentials first (most providers have this)
            if hasattr(provider, 'validate_credentials'):
                if asyncio.iscoroutinefunction(provider.validate_credentials):
                    return await provider.validate_credentials()
                else:
                    return provider.validate_credentials()
            
            # Try validate_connection (CRM adapters)
            elif hasattr(provider, 'validate_connection'):
                if asyncio.iscoroutinefunction(provider.validate_connection):
                    return await provider.validate_connection()
                else:
                    return provider.validate_connection()
            
            # Try is_configured (fallback adapters)
            elif hasattr(provider, 'is_configured'):
                return provider.is_configured()
            
            # If no validation method, assume healthy
            else:
                return True
        
        except Exception as e:
            logger.debug(f"Validation error: {e}")
            return False
    
    def _generate_recommendation(
        self,
        provider_name: str,
        current_status: str,
        issue: str,
    ) -> ProviderRecommendation:
        """
        Generate operator recommendation for unhealthy provider.
        
        Args:
            provider_name: Name of unhealthy provider
            current_status: Current health status
            issue: Description of the issue
            
        Returns:
            ProviderRecommendation with suggested action
        """
        # Map provider names to suggested actions
        action_map = {
            "apollo_enricher": (
                "Check APOLLO_API_KEY environment variable is set and valid. "
                "Verify API rate limits have not been exceeded. "
                "Check Apollo API status page."
            ),
            "dropcontact_verifier": (
                "Check DROPCONTACT_API_KEY environment variable is set and valid. "
                "Verify API rate limits have not been exceeded. "
                "Check Dropcontact API status page."
            ),
            "airtable_crm": (
                "Check AIRTABLE_API_KEY and AIRTABLE_BASE_ID environment variables are set. "
                "Verify Airtable API token is still valid. "
                "Check Airtable connection and permissions."
            ),
            "imap_reply_fetcher": (
                "Check email server credentials and connection settings. "
                "Verify IMAP is enabled on email account. "
                "Check network connectivity to email server."
            ),
            "real_email_gateway": (
                "Check SMTP credentials and connection settings. "
                "Verify network connectivity to SMTP server. "
                "Check Gmail/SMTP configuration."
            ),
        }
        
        # Determine severity
        severity = "critical" if current_status == "unhealthy" else "warning"
        
        # Get suggested action (or generic fallback)
        suggested_action = action_map.get(
            provider_name,
            (
                f"Provider {provider_name} is experiencing issues. "
                "Check configuration and credentials. "
                "Review recent error logs for details."
            ),
        )
        
        return ProviderRecommendation(
            provider_name=provider_name,
            current_status=current_status,
            issue=issue,
            suggested_action=suggested_action,
            severity=severity,
        )
    
    async def start_periodic_checks(
        self,
        interval_seconds: int = 300,  # Default: 5 minutes
    ) -> None:
        """
        Start periodic health checks.
        
        Runs health checks at regular intervals in background.
        
        Args:
            interval_seconds: Seconds between checks (default 300)
        """
        if self._is_running:
            logger.warning("Periodic checks already running")
            return
        
        self._is_running = True
        logger.info(f"Starting periodic health checks (every {interval_seconds}s)")
        
        async def check_loop():
            while self._is_running:
                try:
                    await self.run_full_check()
                except Exception as e:
                    logger.error(f"Periodic check error: {e}")
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
        
        self._check_task = asyncio.create_task(check_loop())
    
    async def stop_periodic_checks(self) -> None:
        """Stop periodic health checks."""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped periodic health checks")
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Get current status report from registry.
        
        Returns:
            Status report with checks and recommendations
        """
        return self.registry.get_status_report()


# Global service instance
_global_service: Optional[SelfCheckService] = None


def get_self_check_service() -> SelfCheckService:
    """
    Get or create the global SelfCheckService.
    
    Returns:
        Global service instance (singleton)
    """
    global _global_service
    if _global_service is None:
        _global_service = SelfCheckService()
        logger.info("Initialized global SelfCheckService")
    return _global_service


def reset_self_check_service() -> None:
    """Reset global service (useful for testing)."""
    global _global_service
    _global_service = None
