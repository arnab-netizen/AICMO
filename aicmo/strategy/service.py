"""Strategy generation service."""

from aicmo.domain.intake import ClientIntake
from aicmo.domain.strategy import StrategyDoc


def generate_strategy(intake: ClientIntake) -> StrategyDoc:
    """
    Generate a marketing strategy from client intake.
    
    Phase 0: Placeholder signature only.
    Phase 1: Will implement by delegating to existing AICMO strategy engine.
    
    Args:
        intake: Normalized client intake data
        
    Returns:
        Generated strategy document
        
    Raises:
        NotImplementedError: Until Phase 1 implementation
    """
    raise NotImplementedError("Implement in Phase 1")
