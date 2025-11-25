"""Auto-recording of outputs as learning examples.

Every time AICMO generates or revises a report, this module extracts key metadata
and stores it in the learning store so future clients can benefit from it.

Learning types supported:
- full_report: Complete generated output (most common)
"""

import datetime as _dt
from typing import Any, Dict, Optional, TYPE_CHECKING
from uuid import uuid4
import json

from backend.learning_store import add_learning_example, LearningExample

if TYPE_CHECKING:
    from backend.schemas import ClientIntakeForm


def _json_default(obj: Any) -> str:
    """JSON serialization fallback for non-standard types like datetime.date."""
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    return str(obj)


def record_learning_from_output(
    brief: "ClientIntakeForm",  # From backend.schemas
    output: Dict[str, Any],
    notes: Optional[str] = None,
) -> None:
    """Record a generated/revised output as a learning example.

    Extracts industry and goal from the brief, serializes the output as JSON,
    and stores it in the learning store for future clients to learn from.

    This function is non-critical and should be wrapped in try-except by the caller.
    It never raises exceptions; all errors are logged.

    Args:
        brief: ClientIntakeForm from the request
        output: Generated output dict (or AICMOOutputReport.model_dump())
        notes: Optional metadata about this learning example
    """
    try:
        # Extract industry from brief.brand.industry
        industry = None
        if hasattr(brief, "brand") and hasattr(brief.brand, "industry"):
            industry = brief.brand.industry

        # Extract goal from brief.goals.primary_goal
        goal = None
        if hasattr(brief, "goals") and hasattr(brief.goals, "primary_goal"):
            goal = brief.goals.primary_goal

        # Extract brand name as source
        source_name = "Unknown"
        if hasattr(brief, "brand") and hasattr(brief.brand, "brand_name"):
            source_name = brief.brand.brand_name

        # Serialize output as formatted JSON (with indentation for readability)
        raw_text = json.dumps(output, indent=2, default=_json_default)

        # Create learning example
        example = LearningExample(
            id=str(uuid4()),
            learning_type="full_report",
            industry=industry,
            goal=goal,
            source_name=source_name,
            notes=notes or "Auto-recorded output",
            raw_text=raw_text,
        )

        # Add to store (this persists to JSON file)
        add_learning_example(example)
        print(f"[Learning] Recorded full_report example from {source_name}")

    except Exception as e:
        # Non-critical – log and continue
        print(f"[Learning] Error recording output: {e}")
