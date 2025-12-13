"""
Module Registry and DI Container - Platform Infrastructure

This is the orchestration foundation that enables modular architecture.
All modules register here; worker uses this to initialize services.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# MODULE REGISTRY
# ─────────────────────────────────────────────────────────────────

@dataclass
class ModuleCapability:
    """Definition of what a module provides."""
    name: str  # e.g., "email.send"
    description: str
    is_critical: bool = False  # If True, worker refuses to start without it


@dataclass
class ModuleInfo:
    """Metadata about a registered module."""
    module_name: str  # e.g., "EmailModule", "ClassificationModule"
    enabled: bool
    capabilities: List[ModuleCapability]
    last_healthy_at: Optional[datetime] = None
    health_status: str = "UNKNOWN"  # HEALTHY, DEGRADED, UNHEALTHY
    error_message: Optional[str] = None


class ModuleRegistry:
    """
    Central registry of all CAM modules.
    
    Worker queries this to determine:
    - Which modules are enabled
    - What capabilities each provides
    - Whether to proceed with execution or degrade
    """
    
    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
    
    def register(self, module_name: str, capabilities: List[str], enabled: bool = True):
        """Register a module with its capabilities."""
        capability_objs = [
            ModuleCapability(
                name=cap,
                description=f"Capability: {cap}",
                is_critical=cap in ["email.send", "inbox.fetch", "alert.send"]
            )
            for cap in capabilities
        ]
        
        self._modules[module_name] = ModuleInfo(
            module_name=module_name,
            enabled=enabled,
            capabilities=capability_objs
        )
        logger.info(f"Registered module: {module_name} (enabled={enabled}, caps={capabilities})")
    
    def get_all(self) -> Dict[str, ModuleInfo]:
        """Get all registered modules."""
        return self._modules
    
    def is_enabled(self, module_name: str) -> bool:
        """Check if module is enabled."""
        module = self._modules.get(module_name)
        return module.enabled if module else False
    
    def set_health(self, module_name: str, is_healthy: bool, message: str = ""):
        """Update module health status."""
        if module_name in self._modules:
            module = self._modules[module_name]
            module.health_status = "HEALTHY" if is_healthy else "UNHEALTHY"
            module.last_healthy_at = datetime.utcnow() if is_healthy else module.last_healthy_at
            module.error_message = message if not is_healthy else None
            logger.info(f"Module {module_name} health: {module.health_status}")
    
    def can_start_worker(self) -> tuple[bool, str]:
        """
        Determine if worker can start.
        
        Returns:
            (can_start: bool, reason: str)
        """
        critical_caps_needed = ["email.send", "inbox.fetch", "alert.send"]
        
        for module_name, module_info in self._modules.items():
            if not module_info.enabled:
                continue
            
            module_caps = [cap.name for cap in module_info.capabilities]
            for cap in critical_caps_needed:
                if cap in module_caps and module_info.health_status == "UNHEALTHY":
                    return False, f"Critical module {module_name} is unhealthy: {module_info.error_message}"
        
        return True, "All critical modules available"


# ─────────────────────────────────────────────────────────────────
# DEPENDENCY INJECTION CONTAINER
# ─────────────────────────────────────────────────────────────────

class DIContainer:
    """
    Dependency injection container.
    
    Worker uses this to instantiate all module services without hard-coding imports.
    This enforces loose coupling.
    """
    
    def __init__(self, registry: ModuleRegistry, db_session):
        self.registry = registry
        self.db_session = db_session
        self._services: Dict[str, Any] = {}
    
    def register_service(self, name: str, service: Any):
        """Register a service instance."""
        self._services[name] = service
        logger.info(f"Registered service: {name}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a registered service."""
        service = self._services.get(name)
        if not service:
            logger.warning(f"Service not found: {name}")
        return service
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services."""
        return self._services
    
    @staticmethod
    def create_default(db_session) -> tuple['DIContainer', ModuleRegistry]:
        """
        Factory: Create and initialize default container with all standard modules.
        
        This is where modules are instantiated and registered.
        """
        from aicmo.cam.services.email_sending_service import EmailSendingService
        from aicmo.cam.services.reply_classifier import ReplyClassifier
        from aicmo.cam.services.follow_up_engine import FollowUpEngine
        from aicmo.cam.services.decision_engine import DecisionEngine
        from aicmo.cam.gateways.inbox_providers.imap import IMAPInboxProvider
        from aicmo.cam.gateways.alert_providers.email_alert import EmailAlertProvider
        
        registry = ModuleRegistry()
        container = DIContainer(registry, db_session)
        
        # Instantiate and register all modules
        try:
            email_module = EmailSendingService(db_session)
            container.register_service("EmailModule", email_module)
            registry.register("EmailModule", ["email.send"], enabled=email_module.is_configured())
            logger.info("✓ EmailModule initialized")
        except Exception as e:
            logger.error(f"Failed to initialize EmailModule: {e}")
            registry.register("EmailModule", ["email.send"], enabled=False)
        
        try:
            classifier = ReplyClassifier()
            container.register_service("ClassificationModule", classifier)
            registry.register("ClassificationModule", ["reply.classify"], enabled=True)
            logger.info("✓ ClassificationModule initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ClassificationModule: {e}")
            registry.register("ClassificationModule", ["reply.classify"], enabled=False)
        
        try:
            followup_module = FollowUpEngine(db_session)
            container.register_service("FollowUpModule", followup_module)
            registry.register("FollowUpModule", ["followup.process"], enabled=True)
            logger.info("✓ FollowUpModule initialized")
        except Exception as e:
            logger.error(f"Failed to initialize FollowUpModule: {e}")
            registry.register("FollowUpModule", ["followup.process"], enabled=False)
        
        try:
            decision_module = DecisionEngine(db_session)
            container.register_service("DecisionModule", decision_module)
            registry.register("DecisionModule", ["decision.compute", "decision.evaluate"], enabled=True)
            logger.info("✓ DecisionModule initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DecisionModule: {e}")
            registry.register("DecisionModule", ["decision.compute", "decision.evaluate"], enabled=False)
        
        try:
            inbox_module = IMAPInboxProvider()
            container.register_service("InboxModule", inbox_module)
            registry.register("InboxModule", ["inbox.fetch"], enabled=inbox_module.is_configured())
            logger.info("✓ InboxModule initialized")
        except Exception as e:
            logger.error(f"Failed to initialize InboxModule: {e}")
            registry.register("InboxModule", ["inbox.fetch"], enabled=False)
        
        try:
            alert_module = EmailAlertProvider()
            container.register_service("AlertModule", alert_module)
            registry.register("AlertModule", ["alert.send"], enabled=alert_module.is_configured())
            logger.info("✓ AlertModule initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AlertModule: {e}")
            registry.register("AlertModule", ["alert.send"], enabled=False)
        
        return container, registry
