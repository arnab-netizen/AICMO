"""
Living Brand Brain (LBB) — BrandMemory Model and Repository

The Living Brand Brain is an AI-aware, contextual memory system for brands.
It learns from every generation, stores insights, and uses them to improve future outputs.

Core Components:
1. BrandMemory: Structured memory of past generations with insights
2. BrandBrainRepository: Persistent storage and retrieval layer
3. generate_with_brand_brain(): Generator wrapper that uses brand memory

Architecture:
- Embeddings-based semantic search (OpenAI, stored in SQLite)
- Persistent storage (SQLite with indexed queries)
- Automatic memory consolidation (forgetting old, low-insight memories)
- Zero-impact on existing generators (wrapper pattern)
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class BrandGenerationInsight:
    """Single insight from a past generation."""
    
    insight_text: str  # "Audience prefers short-form video over long-form"
    confidence: float  # 0.0-1.0: how confident in this insight?
    frequency: int  # How many times have we seen this pattern?
    last_seen: datetime  # When did we last confirm this insight?
    source_context: str  # What brief/scenario revealed this? (e.g., "SWOT analysis")
    generator_type: str  # Which generator created this? (e.g., "persona_generator")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_text": self.insight_text,
            "confidence": self.confidence,
            "frequency": self.frequency,
            "last_seen": self.last_seen.isoformat(),
            "source_context": self.source_context,
            "generator_type": self.generator_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrandGenerationInsight":
        data = data.copy()
        data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        return cls(**data)


@dataclass
class BrandGenerationRecord:
    """Complete record of a generation event (SWOT, persona, etc.)."""
    
    generation_id: str  # UUID of this generation
    generator_type: str  # "swot_generator", "persona_generator", etc.
    brand_id: str  # Which brand?
    brief_id: Optional[str]  # Which brief (if any)?
    
    # Input context
    prompt: str  # What did we ask the LLM?
    brief_summary: Optional[str]  # Summary of the brief used
    
    # Output
    output_json: Dict[str, Any]  # Raw JSON from generator (SWOT, personas, etc.)
    
    # Quality signals
    llm_provider: str  # "claude", "openai", etc.
    completion_time_ms: float  # How long did generation take?
    
    # Extracted insights (automatic)
    extracted_insights: List[BrandGenerationInsight] = field(default_factory=list)
    
    # Human-provided insights (optional, high quality)
    manual_insights: List[BrandGenerationInsight] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.7  # Overall confidence in this record's usefulness
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "generator_type": self.generator_type,
            "brand_id": self.brand_id,
            "brief_id": self.brief_id,
            "prompt": self.prompt,
            "brief_summary": self.brief_summary,
            "output_json": self.output_json,
            "llm_provider": self.llm_provider,
            "completion_time_ms": self.completion_time_ms,
            "extracted_insights": [i.to_dict() for i in self.extracted_insights],
            "manual_insights": [i.to_dict() for i in self.manual_insights],
            "created_at": self.created_at.isoformat(),
            "confidence_score": self.confidence_score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrandGenerationRecord":
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        extracted = [BrandGenerationInsight.from_dict(i) for i in data.pop("extracted_insights", [])]
        manual = [BrandGenerationInsight.from_dict(i) for i in data.pop("manual_insights", [])]
        
        record = cls(
            **data,
            extracted_insights=extracted,
            manual_insights=manual,
        )
        return record


@dataclass
class BrandMemory:
    """
    Complete memory of a brand: all past generations + insights + learned patterns.
    
    This is the "brain" of the brand — it grows over time and informs future generation.
    """
    
    brand_id: str
    brand_name: str
    
    # All past generation records
    generation_history: List[BrandGenerationRecord] = field(default_factory=list)
    
    # Consolidated insights (high-level, pattern-level)
    consolidated_insights: List[BrandGenerationInsight] = field(default_factory=list)
    
    # Learned behaviors (string summaries of what works for this brand)
    learned_behaviors: List[str] = field(default_factory=list)
    
    # Anti-patterns (what doesn't work)
    anti_patterns: List[str] = field(default_factory=list)
    
    # Brand voice/style learned from generations
    brand_voice_summary: Optional[str] = None  # "Casual, emoji-heavy, Gen-Z focused"
    
    # Audience segments learned
    learned_audience_segments: List[str] = field(default_factory=list)
    
    # Topics/themes that resonate
    resonant_topics: List[str] = field(default_factory=list)
    
    # Last update
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    total_generations: int = 0
    avg_generation_quality: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "generation_history": [r.to_dict() for r in self.generation_history],
            "consolidated_insights": [i.to_dict() for i in self.consolidated_insights],
            "learned_behaviors": self.learned_behaviors,
            "anti_patterns": self.anti_patterns,
            "brand_voice_summary": self.brand_voice_summary,
            "learned_audience_segments": self.learned_audience_segments,
            "resonant_topics": self.resonant_topics,
            "updated_at": self.updated_at.isoformat(),
            "total_generations": self.total_generations,
            "avg_generation_quality": self.avg_generation_quality,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrandMemory":
        data = data.copy()
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        history = [BrandGenerationRecord.from_dict(r) for r in data.pop("generation_history", [])]
        insights = [BrandGenerationInsight.from_dict(i) for i in data.pop("consolidated_insights", [])]
        
        return cls(
            **data,
            generation_history=history,
            consolidated_insights=insights,
        )
    
    def get_insight_summary(self, max_insights: int = 5) -> str:
        """
        Get a natural language summary of the top insights for this brand.
        Used as context when prompting generators.
        """
        if not self.consolidated_insights:
            return ""
        
        # Sort by confidence * frequency
        sorted_insights = sorted(
            self.consolidated_insights,
            key=lambda x: x.confidence * x.frequency,
            reverse=True
        )[:max_insights]
        
        insights_text = "\n".join([f"- {i.insight_text}" for i in sorted_insights])
        return f"Brand Memory Insights:\n{insights_text}"
    
    def add_generation_record(self, record: BrandGenerationRecord) -> None:
        """Add a new generation record to this brand's memory."""
        self.generation_history.append(record)
        self.total_generations = len(self.generation_history)
        self.updated_at = datetime.utcnow()
        
        # Update average quality
        if self.generation_history:
            self.avg_generation_quality = sum(
                r.confidence_score for r in self.generation_history
            ) / len(self.generation_history)
    
    def consolidate_insights(self) -> None:
        """
        Process all generation records and extract consolidated insights.
        Should be called periodically to update consolidated_insights.
        """
        # Aggregate all insights from all records
        all_insights = []
        for record in self.generation_history:
            all_insights.extend(record.extracted_insights)
            all_insights.extend(record.manual_insights)
        
        # Group by insight text (fuzzy matching for very similar insights)
        # For now, simple deduplication by exact text match
        insight_map: Dict[str, BrandGenerationInsight] = {}
        for insight in all_insights:
            if insight.insight_text in insight_map:
                # Merge: increase frequency, update last_seen, average confidence
                existing = insight_map[insight.insight_text]
                existing.frequency += 1
                existing.last_seen = max(existing.last_seen, insight.last_seen)
                existing.confidence = (existing.confidence + insight.confidence) / 2
            else:
                insight_map[insight.insight_text] = insight
        
        self.consolidated_insights = list(insight_map.values())
