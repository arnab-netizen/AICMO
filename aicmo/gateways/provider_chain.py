"""
ProviderChain: Multi-provider gateway abstraction with dynamic dispatch and self-healing.

Wraps existing gateway adapters to:
1. Support multiple providers per capability (primary + fallbacks)
2. Monitor provider health and automatically switch to healthy alternatives
3. Report diagnostics for operator visibility
4. Enable self-healing through provider prioritization

This module maintains backward compatibility with existing factory pattern while
adding multi-provider capabilities on top.

SAFETY PATTERNS:
- dry_run support: All operations can run in simulation mode
- No circular imports: Monitoring is light, imported late
- Thread-safe: Uses local lists for provider sorting, never mutates shared state
- Operator-first: Every operation integrates CAM visibility
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Callable, Awaitable
from datetime import datetime, timedelta
import logging
import asyncio

# Avoid circular imports: lightweight typing only at top level
logger = logging.getLogger(__name__)


class ProviderHealth(Enum):
    """Health status of an external service provider."""
    HEALTHY = "healthy"  # Working, acceptable latency
    DEGRADED = "degraded"  # Working but slow or partial failures
    UNHEALTHY = "unhealthy"  # Failing consistently
    UNKNOWN = "unknown"  # Not yet evaluated


@dataclass
class ProviderStatus:
    """Health status and metrics for a provider."""
    provider_name: str
    health: ProviderHealth = ProviderHealth.UNKNOWN
    last_check_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    latency_ms: Optional[float] = None  # Most recent operation latency
    avg_latency_ms: Optional[float] = None  # Rolling average
    error_message: Optional[str] = None
    
    def is_healthy(self) -> bool:
        """Check if provider is in acceptable state."""
        return self.health in (ProviderHealth.HEALTHY, ProviderHealth.DEGRADED)
    
    def needs_health_check(self, max_age_seconds: int = 300) -> bool:
        """Check if health status is stale and needs re-evaluation."""
        if self.last_check_time is None:
            return True
        age = (datetime.now() - self.last_check_time).total_seconds()
        return age > max_age_seconds


class Provider(Protocol):
    """Protocol for any external service provider/adapter.
    
    Represents a real adapter (Apollo, Dropcontact, Airtable, etc.)
    that can be wrapped by ProviderChain for multi-provider support.
    """
    
    async def validate_credentials(self) -> bool:
        """Check if provider has valid credentials/configuration."""
        ...
    
    def get_name(self) -> str:
        """Get provider display name."""
        ...


class ProviderWrapper:
    """
    Wraps a single provider (adapter) instance.
    
    Handles:
    - Method invocation with timing
    - Health status tracking
    - Success/failure recording
    - Graceful error handling
    """
    
    def __init__(
        self,
        provider: Any,
        provider_name: str,
        is_dry_run: bool = False,
        health_threshold_failures: int = 3,
        health_threshold_successes: int = 5,
    ):
        """
        Initialize provider wrapper.
        
        Args:
            provider: The actual adapter instance (Apollo, Dropcontact, etc.)
            provider_name: Display name for logging
            is_dry_run: If True, operations are simulated only
            health_threshold_failures: Mark unhealthy after N consecutive failures
            health_threshold_successes: Mark healthy after N consecutive successes
        """
        self.provider = provider
        self.provider_name = provider_name
        self.is_dry_run = is_dry_run
        self.health_threshold_failures = health_threshold_failures
        self.health_threshold_successes = health_threshold_successes
        
        self.status = ProviderStatus(provider_name=provider_name)
    
    async def invoke(
        self,
        method_name: str,
        *args,
        **kwargs,
    ) -> tuple[bool, Any, Optional[str]]:
        """
        Invoke a method on the wrapped provider with timing and error handling.
        
        Returns:
            Tuple of (success: bool, result: Any, error_message: Optional[str])
        """
        if self.is_dry_run:
            logger.info(f"[DRY_RUN] {self.provider_name}.{method_name}()")
            return (True, None, None)
        
        start_time = datetime.now()
        try:
            # Use getattr for dynamic method dispatch (operator-first, flexible)
            method = getattr(self.provider, method_name, None)
            if method is None:
                error_msg = f"Provider {self.provider_name} has no method {method_name}"
                logger.error(error_msg)
                return (False, None, error_msg)
            
            # Call method - supports both async and sync
            if asyncio.iscoroutinefunction(method):
                result = await method(*args, **kwargs)
            else:
                result = method(*args, **kwargs)
            
            # Record success
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._record_success(latency_ms)
            
            logger.info(
                f"✓ {self.provider_name}.{method_name}() succeeded "
                f"({latency_ms:.1f}ms)"
            )
            return (True, result, None)
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self._record_failure(error_msg)
            logger.warning(
                f"✗ {self.provider_name}.{method_name}() failed: {error_msg}"
            )
            return (False, None, error_msg)
    
    def _record_success(self, latency_ms: float) -> None:
        """Update status after successful invocation."""
        self.status.last_success_time = datetime.now()
        self.status.consecutive_successes += 1
        self.status.consecutive_failures = 0
        self.status.latency_ms = latency_ms
        
        # Update running average latency
        if self.status.avg_latency_ms is None:
            self.status.avg_latency_ms = latency_ms
        else:
            # Exponential moving average (weight: 70% old, 30% new)
            self.status.avg_latency_ms = (
                0.7 * self.status.avg_latency_ms + 0.3 * latency_ms
            )
        
        # Update health status
        if self.status.consecutive_successes >= self.health_threshold_successes:
            self.status.health = ProviderHealth.HEALTHY
        elif self.status.health == ProviderHealth.UNKNOWN:
            self.status.health = ProviderHealth.DEGRADED
        
        self.status.error_message = None
        self.status.last_check_time = datetime.now()
    
    def _record_failure(self, error_message: str) -> None:
        """Update status after failed invocation."""
        self.status.last_failure_time = datetime.now()
        self.status.consecutive_failures += 1
        self.status.consecutive_successes = 0
        self.status.error_message = error_message
        
        if self.status.consecutive_failures >= self.health_threshold_failures:
            self.status.health = ProviderHealth.UNHEALTHY
        elif self.status.health == ProviderHealth.UNKNOWN:
            self.status.health = ProviderHealth.DEGRADED
        
        self.status.last_check_time = datetime.now()


class ProviderChain:
    """
    Multi-provider gateway with automatic fallback and health-based prioritization.
    
    Maintains an ordered list of providers for each capability. Attempts invocation
    on primary provider first, automatically falls back to secondary providers if
    primary fails or is unhealthy.
    
    THREAD-SAFE: Uses local lists for provider sorting, never mutates shared state.
    DRY-RUN: All operations support dry_run mode for testing.
    OPERATOR-FIRST: Every operation logs status for CAM visibility.
    """
    
    def __init__(
        self,
        capability_name: str,
        providers: List[ProviderWrapper],
        is_dry_run: bool = False,
        max_fallback_attempts: int = None,
    ):
        """
        Initialize provider chain for a capability.
        
        Args:
            capability_name: Name of the capability (e.g., "email_sending", "social_posting")
            providers: List of ProviderWrapper instances in priority order
            is_dry_run: If True, simulate all operations
            max_fallback_attempts: If None, try all providers; otherwise limit attempts
        """
        self.capability_name = capability_name
        self.providers = providers
        self.is_dry_run = is_dry_run
        self.max_fallback_attempts = (
            max_fallback_attempts if max_fallback_attempts is not None
            else len(providers)
        )
        
        self._operation_log: List[Dict[str, Any]] = []
    
    async def invoke(
        self,
        method_name: str,
        *args,
        **kwargs,
    ) -> tuple[bool, Any, str]:
        """
        Invoke a method with automatic fallback to healthy providers.
        
        Process:
        1. Sort providers by health (prioritize healthy)
        2. Attempt on primary provider
        3. If fails, try secondary providers
        4. If all fail or unavailable, return failure with last error
        
        Returns:
            Tuple of (success: bool, result: Any, provider_name: str used)
        """
        if not self.providers:
            logger.error(f"No providers configured for {self.capability_name}")
            return (False, None, "NO_PROVIDERS")
        
        # Create local list (thread-safe, no mutation of shared state)
        # Sort by: 1) health status, 2) consecutive successes, 3) latency
        sorted_providers = self._get_sorted_providers()
        
        last_error = "No providers attempted"
        attempts = 0
        
        for wrapper in sorted_providers:
            if attempts >= self.max_fallback_attempts:
                break
            
            attempts += 1
            provider_name = wrapper.provider_name
            
            logger.info(
                f"[{self.capability_name}] Attempt {attempts}: "
                f"invoking {provider_name}.{method_name}()"
            )
            
            success, result, error = await wrapper.invoke(method_name, *args, **kwargs)
            
            # Log operation for audit trail
            self._operation_log.append({
                "capability": self.capability_name,
                "method": method_name,
                "provider": provider_name,
                "success": success,
                "timestamp": datetime.now(),
                "error": error,
            })
            
            if success:
                logger.info(
                    f"✓ [{self.capability_name}] Success via {provider_name}"
                )
                return (True, result, provider_name)
            
            last_error = error
            logger.warning(
                f"✗ [{self.capability_name}] {provider_name} failed, trying next..."
            )
        
        logger.error(
            f"✗ [{self.capability_name}] All {attempts} providers exhausted. "
            f"Last error: {last_error}"
        )
        return (False, None, f"ALL_FAILED ({attempts} attempts)")
    
    def _get_sorted_providers(self) -> List[ProviderWrapper]:
        """
        Get providers sorted by health priority.
        
        Priority order:
        1. Healthy providers (by consecutive successes, then by latency)
        2. Degraded providers
        3. Unhealthy providers (might recover)
        4. Unknown health providers
        
        This is a LOCAL list - never mutates self.providers.
        """
        # Create local copy with sort key
        local_list = [
            (p, self._provider_sort_key(p))
            for p in self.providers
        ]
        
        # Sort by key (highest priority first)
        local_list.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the providers
        return [p for p, _ in local_list]
    
    def _provider_sort_key(self, wrapper: ProviderWrapper) -> tuple:
        """
        Generate sort key for provider prioritization.
        
        Higher values = higher priority.
        Returns tuple: (health_priority, consecutive_successes, negative_latency)
        """
        # Health priority: HEALTHY=3, DEGRADED=2, UNHEALTHY=1, UNKNOWN=0
        health_priority = {
            ProviderHealth.HEALTHY: 3,
            ProviderHealth.DEGRADED: 2,
            ProviderHealth.UNHEALTHY: 1,
            ProviderHealth.UNKNOWN: 0,
        }.get(wrapper.status.health, 0)
        
        # Use consecutive successes (higher = better)
        successes = wrapper.status.consecutive_successes
        
        # Use negative latency (lower latency = higher priority, so negate)
        latency = -(wrapper.status.latency_ms or 9999.0)
        
        return (health_priority, successes, latency)
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Get comprehensive status report for this provider chain.
        
        Includes:
        - Overall capability status
        - Individual provider health
        - Recent operation history
        - Recommendations for operators
        """
        provider_statuses = [
            {
                "name": p.provider_name,
                "health": p.status.health.value,
                "consecutive_failures": p.status.consecutive_failures,
                "consecutive_successes": p.status.consecutive_successes,
                "avg_latency_ms": p.status.avg_latency_ms,
                "last_success": (
                    p.status.last_success_time.isoformat()
                    if p.status.last_success_time
                    else None
                ),
                "last_failure": (
                    p.status.last_failure_time.isoformat()
                    if p.status.last_failure_time
                    else None
                ),
                "error": p.status.error_message,
            }
            for p in self.providers
        ]
        
        # Overall health: healthy if any provider is healthy
        overall_health = "healthy" if any(
            p["health"] == "healthy" for p in provider_statuses
        ) else "degraded" if any(
            p["health"] in ("degraded", "unhealthy") for p in provider_statuses
        ) else "unknown"
        
        return {
            "capability": self.capability_name,
            "overall_health": overall_health,
            "providers": provider_statuses,
            "recent_operations": self._operation_log[-10:],  # Last 10 ops
            "total_operations": len(self._operation_log),
        }


# Module-level registry for all provider chains
# Allows global access without circular imports
_provider_chains: Dict[str, ProviderChain] = {}


def register_provider_chain(chain: ProviderChain) -> None:
    """Register a provider chain for global access (used by factory, monitoring)."""
    _provider_chains[chain.capability_name] = chain
    logger.info(f"Registered ProviderChain: {chain.capability_name}")


def get_provider_chain(capability_name: str) -> Optional[ProviderChain]:
    """Get a registered provider chain by capability name."""
    return _provider_chains.get(capability_name)


def get_all_provider_chains() -> Dict[str, ProviderChain]:
    """Get all registered provider chains (for diagnostics, monitoring)."""
    return dict(_provider_chains)


def clear_provider_chains() -> None:
    """Clear all provider chains (useful for testing)."""
    _provider_chains.clear()


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0 STEP 7: MONITORING INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

def sync_provider_health_with_monitoring() -> None:
    """
    Sync current provider health status with monitoring registry.
    
    Reads health status from all ProviderChain instances and updates the
    SelfCheckRegistry. Useful for integrating real-time health data with
    monitoring dashboard and recommendations.
    
    Call this after operations to keep monitoring registry up-to-date with
    actual provider health metrics from ProviderChain.
    
    Example:
        # After provider operations
        sync_provider_health_with_monitoring()
        
        # Get recommendations for unhealthy providers
        registry = get_registry()
        report = registry.get_status_report()
    """
    try:
        # Import here to avoid circular imports at module load time
        from ..monitoring import get_registry, HealthCheckResult, ProviderRecommendation
    except ImportError:
        logger.debug("Monitoring module not available, skipping sync")
        return
    
    registry = get_registry()
    
    # Iterate all registered provider chains
    for capability_name, chain in _provider_chains.items():
        if chain is None or not hasattr(chain, 'providers'):
            continue
        
        # Sync each provider's health
        for wrapper in chain.providers:
            try:
                # Create health check result from current status
                result = HealthCheckResult(
                    provider_name=wrapper.provider_name,
                    capability=capability_name,
                    timestamp=datetime.now(),
                    success=wrapper.status.is_healthy(),
                    latency_ms=wrapper.status.avg_latency_ms,
                    error_message=wrapper.status.error_message,
                    metadata={
                        "health_status": wrapper.status.health.value,
                        "consecutive_successes": wrapper.status.consecutive_successes,
                        "consecutive_failures": wrapper.status.consecutive_failures,
                    },
                )
                registry.record_health_check(result)
                
                # Generate recommendation if unhealthy
                if not wrapper.status.is_healthy():
                    rec = ProviderRecommendation(
                        provider_name=wrapper.provider_name,
                        current_status=wrapper.status.health.value,
                        issue=wrapper.status.error_message or "Provider not responding",
                        suggested_action=(
                            f"Provider {wrapper.provider_name} is {wrapper.status.health.value}. "
                            f"Check configuration and verify external service connectivity. "
                            f"Fallback providers will be used automatically."
                        ),
                        severity="critical" if wrapper.status.health == ProviderHealth.UNHEALTHY else "warning",
                    )
                    registry.record_recommendation(rec)
            
            except Exception as e:
                logger.debug(f"Failed to sync health for {capability_name}/{wrapper.provider_name}: {e}")
    
    logger.debug("Synced provider health with monitoring registry")


def get_registry():
    """
    Get the monitoring registry (for convenience).
    
    Allows ProviderChain users to easily access registry without importing
    monitoring module directly.
    
    Returns:
        SelfCheckRegistry instance
    """
    try:
        from ..monitoring import get_registry as _get_registry
        return _get_registry()
    except ImportError:
        logger.warning("Monitoring module not available")
        return None
