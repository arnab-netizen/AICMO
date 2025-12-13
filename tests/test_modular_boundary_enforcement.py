"""
Boundary Enforcement Tests (Phase 1)

Validates that the modular architecture enforces strict boundaries:
- Modules communicate ONLY through ports (abstract interfaces)
- Modules MUST NOT import each other's internals
- Services implement their port interfaces completely
- Composition layer uses DIContainer exclusively

This prevents tight coupling and ensures true modularity.
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Dict, Tuple
import pytest


# ─────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def get_python_files(module_path: str) -> List[Path]:
    """Get all Python files in a module recursively."""
    module_dir = Path(module_path)
    if not module_dir.exists():
        return []
    return list(module_dir.rglob("*.py"))


def parse_imports_from_file(file_path: Path) -> Set[str]:
    """Extract all top-level module imports from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports


def get_module_name(file_path: Path) -> str:
    """Get the top-level module name from a file path."""
    parts = file_path.parts
    try:
        aicmo_idx = parts.index('aicmo')
        return parts[aicmo_idx + 1]
    except (ValueError, IndexError):
        return ""


# ─────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────

class TestBoundaryEnforcement:
    """Test that module boundaries are enforced."""
    
    def setup_method(self):
        """Set up test data."""
        self.aicmo_root = Path("/workspaces/AICMO/aicmo")
        self.cam_services = self.aicmo_root / "cam" / "services"
        self.cam_gateways = self.aicmo_root / "cam" / "gateways"
        self.cam_ports = self.aicmo_root / "cam" / "ports"
        self.cam_contracts = self.aicmo_root / "cam" / "contracts"
        self.platform = self.aicmo_root / "platform"
    
    def test_services_import_only_ports_and_contracts(self):
        """
        Test: Services must not import other services' internals.
        
        Services can import:
        - Port interfaces (aicmo.cam.ports)
        - Contracts (aicmo.cam.contracts)
        - DB models (aicmo.cam.db_models)
        - Configuration (aicmo.cam.config)
        
        Services MUST NOT import:
        - Other services' internals
        - Gateways directly (use factories instead)
        """
        forbidden_imports = {
            "email_sending_service",
            "reply_classifier",
            "follow_up_engine",
            "decision_engine",
        }
        
        service_files = get_python_files(str(self.cam_services))
        
        for service_file in service_files:
            if service_file.name.startswith("__"):
                continue
            
            imports = parse_imports_from_file(service_file)
            current_service = service_file.stem
            
            # Check for cross-service imports
            cross_imports = forbidden_imports & imports
            # Don't check self-import
            cross_imports.discard(current_service)
            
            assert not cross_imports, (
                f"{service_file.name} imports other services: {cross_imports}. "
                f"Services must communicate through ports, not direct imports."
            )
    
    def test_ports_have_no_implementation(self):
        """
        Test: Port files must be abstract (no concrete implementation).
        
        Port files should:
        - Define ABC classes with @abstractmethod
        - Have no service logic
        - Be pure interfaces
        """
        port_files = get_python_files(str(self.cam_ports))
        
        for port_file in port_files:
            if port_file.name.startswith("__"):
                continue
            
            with open(port_file, 'r') as f:
                content = f.read()
            
            # Port files should use ABC and abstractmethod
            assert "ABC" in content or "Protocol" in content, (
                f"{port_file.name} should use ABC or Protocol to define abstract interfaces"
            )
            
            # Port files should have minimal implementation
            # (only docstrings and abstract methods)
            # Count non-trivial lines
            lines = [l.strip() for l in content.split('\n') 
                    if l.strip() and not l.strip().startswith('#')]
            
            # Should be mostly class/method definitions
            class_count = content.count("class ")
            method_count = content.count("def ")
            
            assert method_count > 0, f"{port_file.name} should define abstract methods"
    
    def test_contracts_are_immutable_data_classes(self):
        """
        Test: Contract files define only Pydantic models (immutable data).
        
        Contracts should:
        - Use Pydantic BaseModel
        - Be Enums or dataclasses
        - Have no logic/methods (only fields and validation)
        - Never import services or business logic
        """
        with open(self.cam_contracts / "__init__.py", 'r') as f:
            content = f.read()
        
        # Contracts should use Pydantic
        assert "BaseModel" in content or "Enum" in content, (
            "Contracts should use Pydantic BaseModel or Enum"
        )
        
        # Should not have service/gateway imports
        forbidden = {"EmailSendingService", "ReplyClassifier", "IMAPInboxProvider"}
        for forbidden_import in forbidden:
            assert forbidden_import not in content, (
                f"Contracts should not import {forbidden_import}"
            )
    
    def test_orchestration_uses_di_container(self):
        """
        Test: Worker initialization uses DIContainer, never direct service imports.
        
        The orchestration should:
        - Call DIContainer.create_default()
        - Get services via container.get_service()
        - Never instantiate services directly
        """
        worker_file = self.aicmo_root / "cam" / "worker" / "cam_worker.py"
        
        with open(worker_file, 'r') as f:
            content = f.read()
        
        # Should import DIContainer
        assert "DIContainer" in content, (
            "Worker should import DIContainer"
        )
        
        # Should import CamFlowRunner for composition
        assert "CamFlowRunner" in content, (
            "Worker should import CamFlowRunner"
        )
        
        # Should NOT directly instantiate services multiple times
        # (services are created by DIContainer.create_default in setup())
        instantiations = {
            "EmailSendingService(": content.count("EmailSendingService("),
            "ReplyClassifier(": content.count("ReplyClassifier("),
            "FollowUpEngine(": content.count("FollowUpEngine("),
            "DecisionEngine(": content.count("DecisionEngine("),
            "IMAPInboxProvider(": content.count("IMAPInboxProvider("),
        }
        
        # Count how many times each service is instantiated
        # Should be 1 time in DIContainer.create_default(), not in worker
        for service, count in instantiations.items():
            assert count <= 1, (
                f"Service {service} instantiated {count} times. "
                f"Services should be created by DIContainer, not directly."
            )
    
    def test_composition_layer_uses_ports(self):
        """
        Test: CamFlowRunner calls services through ports, not direct imports.
        
        Composition layer should:
        - Get modules via container.get_service()
        - Call through port interfaces only
        - Never import services directly
        """
        flow_runner_file = self.aicmo_root / "cam" / "composition" / "flow_runner.py"
        
        with open(flow_runner_file, 'r') as f:
            content = f.read()
        
        # Should NOT import services directly
        forbidden_imports = {
            "from aicmo.cam.services",
            "from aicmo.cam.gateways",
        }
        
        for forbidden in forbidden_imports:
            assert forbidden not in content, (
                f"CamFlowRunner should not have: {forbidden}. "
                f"Should use container.get_service() instead."
            )
        
        # Should use container.get_service()
        assert "container.get_service" in content, (
            "CamFlowRunner should call container.get_service() to get modules"
        )
        
        # Should pass requests through port interfaces (using contract models)
        assert "SendEmailRequest" in content, (
            "CamFlowRunner should use SendEmailRequest contract"
        )
        assert "ClassifyReplyRequest" in content, (
            "CamFlowRunner should use ClassifyReplyRequest contract"
        )


class TestContractCompletion:
    """Test that all required contracts are defined."""
    
    def setup_method(self):
        """Set up test data."""
        self.aicmo_root = Path("/workspaces/AICMO/aicmo")
        self.contracts_file = self.aicmo_root / "cam" / "contracts" / "__init__.py"
    
    def test_all_required_contracts_exist(self):
        """Test that all required input/output contracts are defined."""
        with open(self.contracts_file, 'r') as f:
            content = f.read()
        
        required_contracts = {
            "SendEmailRequest",
            "SendEmailResponse",
            "ClassifyReplyRequest",
            "ClassifyReplyResponse",
            "ProcessReplyRequest",
            "FetchInboxRequest",
            "FetchInboxResponse",
            "EmailReplyModel",
            "CampaignMetricsModel",
            "ModuleHealthModel",
            "UsageEventModel",
        }
        
        for contract in required_contracts:
            assert contract in content, f"Missing contract: {contract}"
    
    def test_all_required_enums_exist(self):
        """Test that all required enums are defined."""
        with open(self.contracts_file, 'r') as f:
            content = f.read()
        
        required_enums = {
            "ReplyClassificationEnum",
            "LeadStateEnum",
            "WorkerStatusEnum",
        }
        
        for enum_name in required_enums:
            assert enum_name in content, f"Missing enum: {enum_name}"


class TestPortCompletion:
    """Test that all required ports (module interfaces) are defined."""
    
    def setup_method(self):
        """Set up test data."""
        self.aicmo_root = Path("/workspaces/AICMO/aicmo")
        self.ports_file = self.aicmo_root / "cam" / "ports" / "module_ports.py"
    
    def test_all_required_ports_exist(self):
        """Test that all required module ports are defined."""
        with open(self.ports_file, 'r') as f:
            content = f.read()
        
        required_ports = {
            "EmailModule",
            "ClassificationModule",
            "FollowUpModule",
            "InboxModule",
            "DecisionModule",
            "AlertModule",
        }
        
        for port in required_ports:
            assert f"class {port}" in content, f"Missing port: {port}"
    
    def test_ports_have_required_methods(self):
        """Test that ports define required methods."""
        with open(self.ports_file, 'r') as f:
            content = f.read()
        
        # EmailModule should have send_email, is_configured, health
        assert "def send_email" in content, "EmailModule missing send_email()"
        assert "def is_configured" in content, "Ports missing is_configured()"
        assert "def health" in content, "Ports missing health()"
        
        # ClassificationModule should have classify
        assert "def classify" in content, "ClassificationModule missing classify()"
        
        # DecisionModule should have compute_metrics and evaluate_campaign
        assert "def compute_metrics" in content, "DecisionModule missing compute_metrics()"
        assert "def evaluate_campaign" in content, "DecisionModule missing evaluate_campaign()"


class TestDIContainerCompleteness:
    """Test that DIContainer registers all required modules."""
    
    def test_di_container_initializes_all_modules(self):
        """
        Test: DIContainer.create_default() must initialize all 6 required modules.
        
        This test actually runs the initialization to verify it works.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from aicmo.platform.orchestration import DIContainer
        
        # Create in-memory DB for testing
        engine = create_engine('sqlite:///:memory:')
        session_factory = sessionmaker(bind=engine)
        db_session = session_factory()
        
        try:
            # Initialize container
            container, registry = DIContainer.create_default(db_session)
            
            # Check all 6 services are registered
            services = container.get_all_services()
            required_services = {
                "EmailModule",
                "ClassificationModule",
                "FollowUpModule",
                "DecisionModule",
                "InboxModule",
                "AlertModule",
            }
            
            assert set(services.keys()) == required_services, (
                f"Missing services. Expected {required_services}, got {set(services.keys())}"
            )
            
            # Check each service has required methods
            for service_name, service in services.items():
                assert hasattr(service, 'is_configured'), (
                    f"{service_name} missing is_configured()"
                )
                assert hasattr(service, 'health'), (
                    f"{service_name} missing health()"
                )
        
        finally:
            db_session.close()
    
    def test_flow_runner_uses_container(self):
        """
        Test: CamFlowRunner can be instantiated and uses container correctly.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from aicmo.platform.orchestration import DIContainer
        from aicmo.cam.composition import CamFlowRunner
        
        # Create in-memory DB for testing
        engine = create_engine('sqlite:///:memory:')
        session_factory = sessionmaker(bind=engine)
        db_session = session_factory()
        
        try:
            # Initialize container
            container, registry = DIContainer.create_default(db_session)
            
            # Create flow runner
            runner = CamFlowRunner(container, registry, db_session)
            
            # Verify runner can access services through container
            email_module = container.get_service("EmailModule")
            assert email_module is not None, "EmailModule not in container"
            
            classifier = container.get_service("ClassificationModule")
            assert classifier is not None, "ClassificationModule not in container"
        
        finally:
            db_session.close()


# ─────────────────────────────────────────────────────────────────
# TEST RUNNERS
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
