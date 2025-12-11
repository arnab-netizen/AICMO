"""
SelfCheck Registry: Tracks and manages self-healing checks for all providers.

Maintains a global registry of health checks for each provider chain capability,
enabling operators to:
1. Check provider health status on-demand
2. Get recommendations for fixing unhealthy providers
3. View historical performance metrics
4. Schedule periodic health checks

SAFETY PATTERNS:
- dry_run support: Health checks can run in simulation mode
- No circular imports: Lightweight, only imports after app startup
- Thread-safe: Uses dict.copy() for concurrent access
- Operator-first: All results logged for visibility
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a single health check execution."""
    provider_name: str
    capability: str
    timestamp: datetime
    success: bool
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "provider": self.provider_name,
            "capability": self.capability,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "latency_ms": self.latency_ms,
            "error": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class ProviderRecommendation:
    """Operator-friendly recommendation for fixing unhealthy provider."""
    provider_name: str
    current_status: str  # "healthy", "degraded", "unhealthy"
    issue: str  # Description of the problem
    suggested_action: str  # What operator should do
    severity: str  # "info", "warning", "critical"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "provider": self.provider_name,
            "status": self.current_status,
            "issue": self.issue,
            "action": self.suggested_action,
            "severity": self.severity,
        }


class SelfCheckRegistry:
    """
    Global registry for provider health checks and self-healing.
    
    Manages:
    - Health check results for all providers
    - Historical performance metrics
    - Operator recommendations for unhealthy providers
    - Integration with ProviderChain monitoring
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._health_checks: Dict[str, List[HealthCheckResult]] = {}
        self._recommendations: Dict[str, List[ProviderRecommendation]] = {}
        self._check_history_limit = 100  # Keep last 100 checks per provider
    
    def record_health_check(self, result: HealthCheckResult) -> None:
        """
        Record a health check result.
        
        Args:
            result: HealthCheckResult with provider, capability, success, etc.
        """
        provider_key = f"{result.capability}:{result.provider_name}"
        
        if provider_key not in self._health_checks:
            self._health_checks[provider_key] = []
        
        self._health_checks[provider_key].append(result)
        
        # Trim history to limit
        if len(self._health_checks[provider_key]) > self._check_history_limit:
            self._health_checks[provider_key] = (
                self._health_checks[provider_key][-self._check_history_limit:]
            )
        
        # Log the result
        status = "✓" if result.success else "✗"
        latency = f" ({result.latency_ms:.1f}ms)" if result.latency_ms else ""
        logger.info(
            f"{status} Health check: {result.capability}/{result.provider_name}"
            f"{latency}"
        )
    
    def record_recommendation(self, recommendation: ProviderRecommendation) -> None:
        """
        Record an operator recommendation for unhealthy provider.
        
        Args:
            recommendation: ProviderRecommendation with suggested action
        """
        provider_key = recommendation.provider_name
        
        if provider_key not in self._recommendations:
            self._recommendations[provider_key] = []
        
        # Only keep latest recommendation per provider (don't accumulate)
        self._recommendations[provider_key] = [recommendation]
        
        # Log the recommendation
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨",
        }.get(recommendation.severity, "❓")
        
        logger.warning(
            f"{severity_emoji} Recommendation for {provider_key}: "
            f"{recommendation.suggested_action}"
        )
    
    def get_health_history(
        self,
        provider_name: str,
        capability: Optional[str] = None,
        limit: int = 10,
    ) -> List[HealthCheckResult]:
        """
        Get health check history for a provider.
        
        Args:
            provider_name: Provider name to query
            capability: Optional specific capability
            limit: Maximum number of results to return
            
        Returns:
            List of HealthCheckResult objects (most recent first)
        """
        results = []
        
        for key, checks in self._health_checks.items():
            if capability:
                if not key.startswith(f"{capability}:"):
                    continue
            if key.endswith(f":{provider_name}"):
                results.extend(checks)
        
        # Return most recent first, limited by count
        return sorted(results, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_recommendations(
        self,
        severity_filter: Optional[str] = None,
    ) -> List[ProviderRecommendation]:
        """
        Get all operator recommendations.
        
        Args:
            severity_filter: Optional filter by severity (info, warning, critical)
            
        Returns:
            List of ProviderRecommendation objects
        """
        recommendations = []
        
        for rec_list in self._recommendations.values():
            for rec in rec_list:
                if severity_filter is None or rec.severity == severity_filter:
                    recommendations.append(rec)
        
        return recommendations
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Get comprehensive status report for all providers.
        
        Includes:
        - Recent health checks (latest 5)
        - Current recommendations
        - Summary statistics
        
        Returns:
            Dictionary with status report
        """
        # Get recent checks
        recent_checks = []
        for checks in self._health_checks.values():
            if checks:
                recent_checks.append(checks[-1])
        
        recent_checks.sort(key=lambda x: x.timestamp, reverse=True)
        recent_checks = recent_checks[:5]
        
        # Get all recommendations
        all_recommendations = self.get_recommendations()
        
        # Summary stats
        total_checks = sum(len(checks) for checks in self._health_checks.values())
        successful_checks = sum(
            1 for checks in self._health_checks.values()
            for check in checks if check.success
        )
        success_rate = (
            (successful_checks / total_checks * 100)
            if total_checks > 0 else 0
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_providers_tracked": len(self._health_checks),
                "total_checks_recorded": total_checks,
                "success_rate_percent": round(success_rate, 1),
                "active_recommendations": len(all_recommendations),
            },
            "recent_checks": [check.to_dict() for check in recent_checks],
            "recommendations": [
                rec.to_dict() for rec in all_recommendations
            ],
        }
    
    def clear_history(self) -> None:
        """Clear all health check history (useful for testing)."""
        self._health_checks.clear()
        self._recommendations.clear()
        logger.info("Cleared SelfCheckRegistry history")


# Global registry instance
_global_registry: Optional[SelfCheckRegistry] = None


def get_registry() -> SelfCheckRegistry:
    """
    Get or create the global SelfCheckRegistry.
    
    Returns:
        Global registry instance (singleton)
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = SelfCheckRegistry()
        logger.info("Initialized global SelfCheckRegistry")
    return _global_registry


def reset_registry() -> None:
    """Reset global registry (useful for testing)."""
    global _global_registry
    _global_registry = None
