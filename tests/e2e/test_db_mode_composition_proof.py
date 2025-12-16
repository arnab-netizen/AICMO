"""
Test to prove CompositionRoot selects DB repositories in DB mode.

This is the foundational proof that DB-mode E2E is technically wired.
If this test passes, it means the composition root correctly switches
between in-memory and database repositories based on AICMO_PERSISTENCE_MODE.

Does NOT test E2E workflows - only proves repo selection logic.
"""

import os
import pytest
from aicmo.orchestration.composition.root import CompositionRoot


def test_composition_root_selects_db_repos_in_db_mode(monkeypatch):
    """
    Prove: When AICMO_PERSISTENCE_MODE=db, CompositionRoot uses DB repos.
    
    Tests:
    1. Onboarding: _brief_repo is DatabaseBriefRepo
    2. Strategy: _strategy_repo is DatabaseStrategyRepo  
    3. Production: _production_repo is DatabaseProductionRepo (via factory)
    """
    # Set DB mode
    monkeypatch.setenv("AICMO_PERSISTENCE_MODE", "db")
    
    # Force settings reload (singleton may cache)
    from aicmo.shared import config
    config.settings = config.AicmoSettings()
    
    # Instantiate composition root
    root = CompositionRoot()
    
    # Verify DB repos selected
    from aicmo.onboarding.internal.adapters import DatabaseBriefRepo
    from aicmo.strategy.internal.repositories_db import DatabaseStrategyRepo
    from aicmo.production.internal.repositories_db import DatabaseProductionRepo
    
    assert isinstance(root._brief_repo, DatabaseBriefRepo), \
        f"Expected DatabaseBriefRepo, got {type(root._brief_repo).__name__}"
    
    assert isinstance(root._strategy_repo, DatabaseStrategyRepo), \
        f"Expected DatabaseStrategyRepo, got {type(root._strategy_repo).__name__}"
    
    assert isinstance(root._production_repo, DatabaseProductionRepo), \
        f"Expected DatabaseProductionRepo, got {type(root._production_repo).__name__}"


def test_composition_root_selects_inmemory_repos_in_inmemory_mode(monkeypatch):
    """
    Prove: When AICMO_PERSISTENCE_MODE=inmemory, CompositionRoot uses in-memory repos.
    
    Tests same repos as DB mode test to prove bidirectional switching.
    """
    # Set in-memory mode
    monkeypatch.setenv("AICMO_PERSISTENCE_MODE", "inmemory")
    
    # Force settings reload
    from aicmo.shared import config
    config.settings = config.AicmoSettings()
    
    # Instantiate composition root
    root = CompositionRoot()
    
    # Verify in-memory repos selected
    from aicmo.onboarding.internal.adapters import InMemoryBriefRepo
    from aicmo.strategy.internal.repositories_mem import InMemoryStrategyRepo
    from aicmo.production.internal.repositories_mem import InMemoryProductionRepo
    
    assert isinstance(root._brief_repo, InMemoryBriefRepo), \
        f"Expected InMemoryBriefRepo, got {type(root._brief_repo).__name__}"
    
    assert isinstance(root._strategy_repo, InMemoryStrategyRepo), \
        f"Expected InMemoryStrategyRepo, got {type(root._strategy_repo).__name__}"
    
    assert isinstance(root._production_repo, InMemoryProductionRepo), \
        f"Expected InMemoryProductionRepo, got {type(root._production_repo).__name__}"


def test_composition_root_default_mode_is_inmemory(monkeypatch):
    """
    Prove: Without explicit AICMO_PERSISTENCE_MODE, default is in-memory.
    
    This is the safe default for tests that don't set env vars.
    """
    # Clear env var to test default
    monkeypatch.delenv("AICMO_PERSISTENCE_MODE", raising=False)
    
    # Force settings reload
    from aicmo.shared import config
    config.settings = config.AicmoSettings()
    
    # Instantiate composition root
    root = CompositionRoot()
    
    # Verify in-memory repos selected (default)
    from aicmo.onboarding.internal.adapters import InMemoryBriefRepo
    
    assert isinstance(root._brief_repo, InMemoryBriefRepo), \
        "Expected InMemoryBriefRepo as default, got {type(root._brief_repo).__name__}"


def test_workflow_factory_uses_correct_repos_in_db_mode(monkeypatch):
    """
    Prove: create_client_to_delivery_workflow() returns workflow with DB repos in DB mode.
    
    This is the critical test for E2E - the workflow factory must wire DB repos.
    """
    # Set DB mode
    monkeypatch.setenv("AICMO_PERSISTENCE_MODE", "db")
    
    # Force settings reload
    from aicmo.shared import config
    config.settings = config.AicmoSettings()
    
    # Instantiate composition root and get workflow
    root = CompositionRoot()
    workflow = root.create_client_to_delivery_workflow()
    
    # Verify workflow uses adapters wired to DB repos
    # Check by inspecting adapter's repo attribute
    from aicmo.onboarding.internal.adapters import DatabaseBriefRepo
    from aicmo.strategy.internal.repositories_db import DatabaseStrategyRepo
    
    assert isinstance(workflow._brief_normalize._repo, DatabaseBriefRepo), \
        f"Workflow brief adapter should use DatabaseBriefRepo, got {type(workflow._brief_normalize._repo).__name__}"
    
    assert isinstance(workflow._strategy_generate._repo, DatabaseStrategyRepo), \
        f"Workflow strategy adapter should use DatabaseStrategyRepo, got {type(workflow._strategy_generate._repo).__name__}"


def test_workflow_factory_uses_correct_repos_in_inmemory_mode(monkeypatch):
    """
    Prove: create_client_to_delivery_workflow() returns workflow with in-memory repos in inmemory mode.
    """
    # Set in-memory mode
    monkeypatch.setenv("AICMO_PERSISTENCE_MODE", "inmemory")
    
    # Force settings reload
    from aicmo.shared import config
    config.settings = config.AicmoSettings()
    
    # Instantiate composition root and get workflow
    root = CompositionRoot()
    workflow = root.create_client_to_delivery_workflow()
    
    # Verify workflow uses adapters wired to in-memory repos
    from aicmo.onboarding.internal.adapters import InMemoryBriefRepo
    from aicmo.strategy.internal.repositories_mem import InMemoryStrategyRepo
    
    assert isinstance(workflow._brief_normalize._repo, InMemoryBriefRepo), \
        f"Workflow brief adapter should use InMemoryBriefRepo, got {type(workflow._brief_normalize._repo).__name__}"
    
    assert isinstance(workflow._strategy_generate._repo, InMemoryStrategyRepo), \
        f"Workflow strategy adapter should use InMemoryStrategyRepo, got {type(workflow._strategy_generate._repo).__name__}"
