"""
Composition Layer - Orchestrates modules through ports

This module implements the composition layer that wires together
all CAM modules to execute the autonomous worker cycle.

Public API:
- CamFlowRunner: Main orchestrator class
- CycleResult: Result of one worker cycle
- StepResult: Result of one step in the cycle
"""

from .flow_runner import CamFlowRunner, CycleResult, StepResult

__all__ = ["CamFlowRunner", "CycleResult", "StepResult"]
