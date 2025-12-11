"""
generate_with_brand_brain: Wrapper function that enhances generators with brand memory.

This is the integration point where generators are enhanced with:
1. Brand memory context (past insights)
2. Automatic insight extraction from outputs
3. Memory persistence
4. Quality signals for learning

Usage:
    from aicmo.brand.brain import generate_with_brand_brain
    
    # Wrap any generator call
    result = generate_with_brand_brain(
        generator_func=swot_generator.generate_swot,
        brand_id=brand_id,
        generator_type="swot_generator",
        kwargs={"brief": brief}
    )
    # Returns: (result, insights_extracted)
"""

import json
import logging
import uuid
import time
from typing import Callable, Dict, Any, Tuple, Optional, List
from datetime import datetime

from aicmo.brand.memory import BrandMemory, BrandGenerationRecord, BrandGenerationInsight
from aicmo.brand.repository import BrandBrainRepository
from aicmo.io.client_reports import ClientInputBrief

logger = logging.getLogger(__name__)


class BrandBrainInsightExtractor:
    """
    Automatic insight extraction from generator outputs.
    
    Each generator type (SWOT, Persona, etc.) has different output structure,
    so we need type-specific extraction logic.
    """
    
    @staticmethod
    def extract_from_swot(swot_data: Dict[str, Any], brief: Optional[ClientInputBrief] = None) -> List[BrandGenerationInsight]:
        """Extract insights from SWOT analysis."""
        insights = []
        
        if not isinstance(swot_data, dict):
            return insights
        
        # Extract patterns from opportunities and strengths
        for opportunity in swot_data.get("opportunities", []):
            if isinstance(opportunity, dict):
                text = opportunity.get("opportunity", "")
            else:
                text = str(opportunity)
            
            if text:
                insights.append(BrandGenerationInsight(
                    insight_text=f"Opportunity identified: {text}",
                    confidence=0.8,
                    frequency=1,
                    last_seen=datetime.utcnow(),
                    source_context="SWOT analysis",
                    generator_type="swot_generator",
                ))
        
        for strength in swot_data.get("strengths", []):
            if isinstance(strength, dict):
                text = strength.get("strength", "")
            else:
                text = str(strength)
            
            if text:
                insights.append(BrandGenerationInsight(
                    insight_text=f"Brand strength: {text}",
                    confidence=0.85,
                    frequency=1,
                    last_seen=datetime.utcnow(),
                    source_context="SWOT analysis",
                    generator_type="swot_generator",
                ))
        
        return insights
    
    @staticmethod
    def extract_from_personas(personas_data: List[Dict[str, Any]], brief: Optional[ClientInputBrief] = None) -> List[BrandGenerationInsight]:
        """Extract insights from persona generation."""
        insights = []
        
        if not isinstance(personas_data, list):
            return insights
        
        for persona in personas_data:
            if isinstance(persona, dict):
                name = persona.get("name", "Unknown")
                motivation = persona.get("motivation", "")
                pain_point = persona.get("pain_point", "")
                
                if motivation:
                    insights.append(BrandGenerationInsight(
                        insight_text=f"Persona '{name}' is motivated by: {motivation}",
                        confidence=0.75,
                        frequency=1,
                        last_seen=datetime.utcnow(),
                        source_context="Persona generation",
                        generator_type="persona_generator",
                    ))
                
                if pain_point:
                    insights.append(BrandGenerationInsight(
                        insight_text=f"Key pain point: {pain_point}",
                        confidence=0.8,
                        frequency=1,
                        last_seen=datetime.utcnow(),
                        source_context="Persona generation",
                        generator_type="persona_generator",
                    ))
        
        return insights
    
    @staticmethod
    def extract_from_social_calendar(posts_data: List[Dict[str, Any]], brief: Optional[ClientInputBrief] = None) -> List[BrandGenerationInsight]:
        """Extract insights from social calendar generation."""
        insights = []
        
        if not isinstance(posts_data, list):
            return insights
        
        # Extract platform preferences
        platforms_used = set()
        themes_used = set()
        
        for post in posts_data:
            if isinstance(post, dict):
                platforms_used.add(post.get("platform", ""))
                themes_used.add(post.get("theme", ""))
        
        if platforms_used:
            insights.append(BrandGenerationInsight(
                insight_text=f"Social platforms: {', '.join(p for p in platforms_used if p)}",
                confidence=0.7,
                frequency=1,
                last_seen=datetime.utcnow(),
                source_context="Social calendar generation",
                generator_type="social_calendar_generator",
            ))
        
        return insights
    
    @staticmethod
    def extract_insights(
        output: Any,
        generator_type: str,
        brief: Optional[ClientInputBrief] = None
    ) -> List[BrandGenerationInsight]:
        """
        Extract insights from generator output.
        
        Dispatches to type-specific extraction methods.
        """
        if generator_type == "swot_generator":
            return BrandBrainInsightExtractor.extract_from_swot(output, brief)
        elif generator_type == "persona_generator":
            return BrandBrainInsightExtractor.extract_from_personas(output, brief)
        elif generator_type == "social_calendar_generator":
            return BrandBrainInsightExtractor.extract_from_social_calendar(output, brief)
        else:
            logger.warning(f"No insight extraction defined for generator type: {generator_type}")
            return []


def generate_with_brand_brain(
    generator_func: Callable,
    brand_id: str,
    generator_type: str,
    kwargs: Dict[str, Any],
    brief: Optional[ClientInputBrief] = None,
    llm_provider: str = "unknown",
    repo: Optional[BrandBrainRepository] = None,
) -> Tuple[Any, List[BrandGenerationInsight]]:
    """
    Wrapper that enhances any generator with brand memory.
    
    Process:
    1. Load brand memory from repository
    2. Add memory context to generator arguments (if applicable)
    3. Call the generator
    4. Extract insights from output
    5. Save generation record to memory
    6. Return result + extracted insights
    
    Args:
        generator_func: The generator function to call (e.g., swot_generator.generate_swot)
        brand_id: Which brand this generation is for
        generator_type: Type of generator ("swot_generator", etc.)
        kwargs: Arguments to pass to the generator
        brief: The brief being used (if available)
        llm_provider: Which LLM provider was used
        repo: BrandBrainRepository instance (uses default if None)
    
    Returns:
        (output, insights): The generator's output and extracted insights
    """
    if repo is None:
        repo = BrandBrainRepository()
    
    try:
        # Load brand memory
        memory = repo.load_memory(brand_id)
        if memory is None:
            memory = BrandMemory(
                brand_id=brand_id,
                brand_name=brief.brand.brand_name if brief else brand_id,
            )
            logger.info(f"Created new brand memory for {brand_id}")
        
        # Add memory context to generator arguments if brief is provided
        # Some generators might use this context to improve outputs
        if brief:
            # This is optional - not all generators will use it
            brief._brand_memory_insights = memory.get_insight_summary()
        
        # Call the generator
        start_time = time.time()
        output = generator_func(**kwargs)
        completion_time_ms = (time.time() - start_time) * 1000
        
        # Extract insights from output
        extracted_insights = BrandBrainInsightExtractor.extract_insights(
            output,
            generator_type,
            brief,
        )
        
        # Create generation record
        generation_id = str(uuid.uuid4())
        record = BrandGenerationRecord(
            generation_id=generation_id,
            generator_type=generator_type,
            brand_id=brand_id,
            brief_id=getattr(brief, "brief_id", None) if brief else None,
            prompt="",  # Not captured for now (would need to be passed in)
            brief_summary=brief.goal.primary_goal if brief and brief.goal else None,
            output_json=output if isinstance(output, dict) else {"output": str(output)},
            llm_provider=llm_provider,
            completion_time_ms=completion_time_ms,
            extracted_insights=extracted_insights,
            confidence_score=0.7,  # Default; could be refined based on output quality
        )
        
        # Add record to memory and save
        memory.add_generation_record(record)
        memory.consolidate_insights()
        repo.save_memory(memory)
        
        logger.info(
            f"Generation {generation_id} for brand {brand_id} "
            f"completed in {completion_time_ms:.0f}ms, "
            f"extracted {len(extracted_insights)} insights"
        )
        
        return output, extracted_insights
    
    except Exception as e:
        logger.error(f"Error in generate_with_brand_brain: {e}", exc_info=True)
        # On error, still return output but with empty insights
        try:
            output = generator_func(**kwargs)
            return output, []
        except Exception as inner_e:
            logger.error(f"Generator function itself failed: {inner_e}")
            raise


def get_brand_memory(brand_id: str, repo: Optional[BrandBrainRepository] = None) -> Optional[BrandMemory]:
    """Convenience function to retrieve brand memory without generating."""
    if repo is None:
        repo = BrandBrainRepository()
    return repo.load_memory(brand_id)


def get_brand_insights(
    brand_id: str,
    days: int = 30,
    limit: int = 10,
    repo: Optional[BrandBrainRepository] = None
) -> List[BrandGenerationInsight]:
    """Convenience function to retrieve recent insights for a brand."""
    if repo is None:
        repo = BrandBrainRepository()
    return repo.get_recent_insights(brand_id, days=days, limit=limit)
