"""
Test public API contract imports.

Verifies that all primary domain models and orchestrators are importable from package root.
This ensures the public API surface is stable and complete.
"""

import pytest


def test_cam_domain_import():
    """Test that CAM domain models are importable from public API."""
    try:
        from aicmo.cam import Lead, Campaign, Channel, LeadStatus
        
        assert Lead is not None
        assert Campaign is not None
        assert Channel is not None
        assert LeadStatus is not None
    except ImportError as e:
        pytest.fail(f"CAM domain models not exported: {e}")


def test_cam_orchestrator_import():
    """Test that CAM orchestrator models are importable."""
    try:
        from aicmo.cam.orchestrator import OrchestratorRunDB
        
        assert OrchestratorRunDB is not None
    except ImportError as e:
        pytest.fail(f"CAM orchestrator models not exported: {e}")


def test_creative_public_api_import():
    """Test that creative generation is importable from public API."""
    try:
        from aicmo.creative import CreativeDirection, generate_creative_directions
        
        assert CreativeDirection is not None
        assert callable(generate_creative_directions)
    except ImportError as e:
        pytest.fail(f"Creative API not exported: {e}")


def test_social_public_api_import():
    """Test that social service is importable from public API."""
    try:
        from aicmo.social import (
            generate_listening_report,
            analyze_trends,
            discover_influencers,
            create_influencer_campaign,
        )
        
        assert callable(generate_listening_report)
        assert callable(analyze_trends)
        assert callable(discover_influencers)
        assert callable(create_influencer_campaign)
    except ImportError as e:
        pytest.fail(f"Social API not exported: {e}")


def test_delivery_public_api_import():
    """Test that delivery gate is importable from public API."""
    try:
        from aicmo.delivery import DeliveryGate, check_delivery_allowed, block_delivery
        
        assert DeliveryGate is not None
        assert callable(check_delivery_allowed)
        assert callable(block_delivery)
    except ImportError as e:
        pytest.fail(f"Delivery API not exported: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
