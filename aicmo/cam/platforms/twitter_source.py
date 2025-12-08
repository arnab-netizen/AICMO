"""
Twitter/X Lead Discovery Source.

⚠️ ETHICAL COMPLIANCE REQUIRED ⚠️

This module MUST use official Twitter/X APIs only.
NO web scraping, NO headless browsers, NO ToS violations.

All search functionality must go through:
- Twitter API v2 (with proper authentication)
- Existing gateway adapters in aicmo.gateways.*

For now, this is a STUB that returns empty results or mock data in tests.
Real implementation requires proper API credentials and compliance review.
"""

from typing import List

from aicmo.cam.discovery_domain import DiscoveryCriteria, DiscoveredProfile, Platform


def search(criteria: DiscoveryCriteria) -> List[DiscoveredProfile]:
    """
    Search Twitter/X for profiles matching criteria.
    
    ⚠️ STUB IMPLEMENTATION ⚠️
    
    Real implementation must:
    - Use Twitter API v2 only
    - Respect rate limits
    - Follow Twitter's Developer Agreement
    - Not use web scraping or browser automation
    
    Args:
        criteria: Search criteria (keywords, location, followers, etc.)
        
    Returns:
        List of discovered profiles (currently empty stub)
    """
    # TODO: Implement with official Twitter API v2 when ready
    # For now, return empty list to avoid ToS violations
    return []
