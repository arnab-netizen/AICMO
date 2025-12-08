"""
LinkedIn Lead Discovery Source.

⚠️ ETHICAL COMPLIANCE REQUIRED ⚠️

This module MUST use official LinkedIn APIs only.
NO web scraping, NO headless browsers, NO ToS violations.

All search functionality must go through:
- LinkedIn Marketing Developer Platform APIs
- LinkedIn Recruiter API (if licensed)
- Existing gateway adapters in aicmo.gateways.*

For now, this is a STUB that returns empty results or mock data in tests.
Real implementation requires proper API credentials and compliance review.
"""

from typing import List

from aicmo.cam.discovery_domain import DiscoveryCriteria, DiscoveredProfile, Platform


def search(criteria: DiscoveryCriteria) -> List[DiscoveredProfile]:
    """
    Search LinkedIn for profiles matching criteria.
    
    ⚠️ STUB IMPLEMENTATION ⚠️
    
    Real implementation must:
    - Use LinkedIn official APIs only
    - Respect rate limits
    - Follow LinkedIn's ToS for automated data collection
    - Not use web scraping or browser automation
    
    Args:
        criteria: Search criteria (keywords, location, role, etc.)
        
    Returns:
        List of discovered profiles (currently empty stub)
    """
    # TODO: Implement with official LinkedIn API when ready
    # For now, return empty list to avoid ToS violations
    return []
