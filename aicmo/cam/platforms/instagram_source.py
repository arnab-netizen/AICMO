"""
Instagram Lead Discovery Source.

⚠️ ETHICAL COMPLIANCE REQUIRED ⚠️

This module MUST use official Instagram APIs only.
NO web scraping, NO headless browsers, NO ToS violations.

All search functionality must go through:
- Instagram Graph API (with proper authentication)
- Instagram Business Account APIs
- Existing gateway adapters in aicmo.gateways.*

For now, this is a STUB that returns empty results or mock data in tests.
Real implementation requires proper API credentials and compliance review.
"""

from typing import List

from aicmo.cam.discovery_domain import DiscoveryCriteria, DiscoveredProfile, Platform


def search(criteria: DiscoveryCriteria) -> List[DiscoveredProfile]:
    """
    Search Instagram for profiles matching criteria.
    
    ⚠️ STUB IMPLEMENTATION ⚠️
    
    Real implementation must:
    - Use Instagram Graph API only
    - Respect rate limits
    - Follow Instagram's Platform Policy
    - Not use web scraping or browser automation
    
    Args:
        criteria: Search criteria (keywords, hashtags, location, etc.)
        
    Returns:
        List of discovered profiles (currently empty stub)
    """
    # TODO: Implement with official Instagram API when ready
    # For now, return empty list to avoid ToS violations
    return []
