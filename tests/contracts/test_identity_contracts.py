"""
Contract tests for identity module.

Validates:
- CONTRACT_VERSION exists
- Ports are abstract interfaces
- DTOs validate correctly
- Events have required fields
- No internal imports in API layer
"""

import pytest
from abc import ABC
from pydantic import BaseModel, ValidationError


def test_identity_contract_version_exists():
    """CONTRACT_VERSION must exist and equal '1.0'."""
    from aicmo.identity.api import CONTRACT_VERSION
    
    assert CONTRACT_VERSION == "1.0", f"Expected CONTRACT_VERSION='1.0', got '{CONTRACT_VERSION}'"


def test_identity_ports_are_abstract():
    """All ports must be ABC subclasses with abstractmethods."""
    import inspect
    from aicmo.identity import api
    
    # Get all port classes (end with 'Port')
    port_classes = [
        obj for name, obj in inspect.getmembers(api.ports, inspect.isclass)
        if name.endswith("Port") and not name.startswith("_")
    ]
    
    assert len(port_classes) > 0, "No port classes found - module must define at least one port"
    
    for port_cls in port_classes:
        # Must be ABC subclass
        assert issubclass(port_cls, ABC), f"{port_cls.__name__} must inherit from ABC"
        
        # Must have at least one abstract method
        abstract_methods = [
            name for name in dir(port_cls)
            if getattr(getattr(port_cls, name, None), "__isabstractmethod__", False)
        ]
        assert len(abstract_methods) > 0, f"{port_cls.__name__} must have at least one @abstractmethod"


def test_identity_dtos_are_pydantic():
    """All DTOs must be Pydantic BaseModel subclasses."""
    import inspect
    from aicmo.identity import api
    
    dto_classes = [
        obj for name, obj in inspect.getmembers(api.dtos, inspect.isclass)
        if name.endswith("DTO") and not name.startswith("_")
    ]
    
    assert len(dto_classes) > 0, "No DTO classes found - module must define at least one DTO"
    
    for dto_cls in dto_classes:
        assert issubclass(dto_cls, BaseModel), f"{dto_cls.__name__} must inherit from Pydantic BaseModel"


def test_identity_events_have_required_fields():
    """All events must have event_id, occurred_at, correlation_id."""
    import inspect
    from aicmo.identity import api
    from aicmo.shared.events import DomainEvent
    
    event_classes = [
        obj for name, obj in inspect.getmembers(api.events, inspect.isclass)
        if not name.startswith("_") and name != "DomainEvent"
    ]
    
    # Events are optional - some modules may not emit events yet
    if len(event_classes) == 0:
        pytest.skip("No events defined for identity module yet")
    
    for event_cls in event_classes:
        # Must inherit from DomainEvent (which has required fields)
        assert issubclass(event_cls, DomainEvent), f"{event_cls.__name__} must inherit from DomainEvent"


def test_identity_api_has_no_internal_imports():
    """API layer must not import from internal/ or domain/."""
    import inspect
    from aicmo.identity import api
    
    forbidden_patterns = [".internal", "aicmo.domain"]
    
    # Check ports
    ports_source = inspect.getsourcefile(api.ports)
    with open(ports_source) as f:
        ports_content = f.read()
    
    for pattern in forbidden_patterns:
        assert pattern not in ports_content, f"ports.py imports from {pattern} - violates encapsulation"
    
    # Check dtos
    dtos_source = inspect.getsourcefile(api.dtos)
    with open(dtos_source) as f:
        dtos_content = f.read()
    
    for pattern in forbidden_patterns:
        assert pattern not in dtos_content, f"dtos.py imports from {pattern} - violates encapsulation"
