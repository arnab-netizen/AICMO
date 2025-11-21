"""Learning store: JSON-based memory for reference decks and reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Literal, Optional


LEARNING_STORE_PATH = Path("data/aicmo_learning_store.json")
LEARNING_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


LearningType = Literal[
    "strategy_deck",
    "campaign_blueprint",
    "persona_pack",
    "calendar_format",
    "creative_rationale",
    "full_report",
]


@dataclass
class LearningExample:
    """A stored reference example for AICMO to learn from."""

    id: str
    learning_type: LearningType
    industry: Optional[str]
    goal: Optional[str]
    source_name: str  # e.g. "Ogilvy_B2B_SaaS_Deck"
    notes: Optional[str]
    raw_text: str  # extracted plain text or JSON string


def _load_store() -> List[LearningExample]:
    """Load all learning examples from JSON file."""
    if not LEARNING_STORE_PATH.exists():
        return []
    data = json.loads(LEARNING_STORE_PATH.read_text(encoding="utf-8"))
    return [LearningExample(**item) for item in data]


def _save_store(items: List[LearningExample]) -> None:
    """Save learning examples to JSON file."""
    LEARNING_STORE_PATH.write_text(
        json.dumps([asdict(i) for i in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_learning_example(example: LearningExample) -> None:
    """Add a new learning example to the store."""
    items = _load_store()
    items.append(example)
    _save_store(items)


def get_relevant_examples(
    learning_type: LearningType,
    industry: Optional[str] = None,
    goal: Optional[str] = None,
    max_examples: int = 3,
) -> List[LearningExample]:
    """
    Get relevant learning examples by type and optional industry/goal match.

    Simple relevance scoring:
      - match by type (required)
      - prefer same industry (+2 points)
      - prefer same goal (+1 point)
    """
    items = _load_store()
    filtered: List[LearningExample] = [i for i in items if i.learning_type == learning_type]

    def score(ex: LearningExample) -> int:
        s = 0
        if industry and ex.industry and ex.industry.lower() == industry.lower():
            s += 2
        if goal and ex.goal and ex.goal.lower() == (goal or "").lower():
            s += 1
        return s

    filtered.sort(key=score, reverse=True)
    return filtered[:max_examples]


def get_all_stats() -> Dict[str, int]:
    """Quick stats on stored learning examples by type."""
    items = _load_store()
    by_type: Dict[str, int] = {}
    for ex in items:
        by_type[ex.learning_type] = by_type.get(ex.learning_type, 0) + 1
    return by_type
