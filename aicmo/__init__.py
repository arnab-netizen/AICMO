"""
AICMO - Modular Marketing Agent

New modular architecture organized by domain:
- domain/: Pydantic models and enums
- core/: DB, config, workflow state machine
- strategy/: Intake -> strategy docs
- creatives/: Strategy -> creative assets
- delivery/: Projects, orchestrator, HTTP layer
- gateways/: Ports & adapters for execution
- acquisition/: Lead finding and enrichment
- cam/: Client Acquisition Mode
"""

__version__ = "0.1.0"
