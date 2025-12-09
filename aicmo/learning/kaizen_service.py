"""
Kaizen Service - Learning Consumer

Aggregates learning events to produce actionable guidance for generation.
Turns raw events into KaizenContext that biases future decisions.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import sqlite3
import json
import os
from datetime import datetime, timedelta

from aicmo.memory.engine import DEFAULT_DB_PATH


class KaizenContext(BaseModel):
    """
    Structured learning context for biasing generation.
    
    Produced by analyzing historical events and outcomes.
    Fed back into generators to improve future outputs.
    """
    
    # Content patterns
    recommended_tones: List[str] = []
    risky_patterns: List[str] = []
    preferred_platforms: List[str] = []
    banned_phrases: List[str] = []
    
    # Past winners (examples of high-performing content)
    past_winners: List[Dict[str, Any]] = []
    
    # Strategy insights
    successful_pillars: List[str] = []
    high_performing_hooks: List[str] = []
    
    # Execution insights
    best_post_times: List[str] = []
    optimal_content_length: Optional[Dict[str, int]] = None  # platform -> word_count
    
    # Client/segment insights
    typical_clarification_count: Optional[int] = None
    expected_response_time_hours: Optional[float] = None
    
    # Channel effectiveness
    channel_performance: Dict[str, float] = {}  # channel -> effectiveness_score
    
    # ICP patterns
    high_clarity_segments: List[str] = []
    problematic_segments: List[str] = []
    
    # Pack insights
    pack_success_rates: Dict[str, float] = {}  # pack_key -> success_rate
    
    # Confidence score
    confidence: float = 0.0  # 0-100, based on sample size
    sample_size: int = 0


class KaizenService:
    """
    Kaizen consumer that turns events into actionable guidance.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Kaizen service.
        
        Args:
            db_path: Optional path to memory database (uses AICMO_MEMORY_DB if not provided)
        """
        self.db_path = db_path or os.getenv("AICMO_MEMORY_DB", DEFAULT_DB_PATH)
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def _query_events(
        self,
        event_types: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Query learning events from memory database.
        
        Args:
            event_types: Optional filter by event types
            project_id: Optional filter by project
            tags: Optional filter by tags
            days_back: How many days back to look
            
        Returns:
            List of event dicts
        """
        conn = self._get_conn()
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        query = "SELECT title, text, tags, created_at FROM memory_items WHERE kind='learning_event' AND created_at >= ?"
        params = [cutoff_date]
        
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        events = []
        for title, text, tags_json, created_at in rows:
            event_tags = json.loads(tags_json) if tags_json else []
            
            # Extract event type from title
            event_type = title.split()[0] if title else "UNKNOWN"
            
            # Filter by event types if specified
            if event_types and event_type not in event_types:
                continue
            
            # Filter by tags if specified
            if tags and not any(tag in event_tags for tag in tags):
                continue
            
            # Parse details from text
            details = {}
            if "Details:" in text:
                try:
                    details_str = text.split("Details:")[1].strip()
                    details = json.loads(details_str)
                except:
                    pass
            
            events.append({
                "type": event_type,
                "title": title,
                "text": text,
                "tags": event_tags,
                "created_at": created_at,
                "details": details
            })
        
        return events
    
    def build_context_for_project(self, project_id: str) -> KaizenContext:
        """
        Build Kaizen context specific to a project.
        
        Analyzes events related to this project to provide
        project-specific guidance.
        
        Args:
            project_id: Project identifier
            
        Returns:
            KaizenContext with project-specific insights
        """
        events = self._query_events(project_id=project_id)
        
        context = KaizenContext()
        context.sample_size = len(events)
        
        # Calculate confidence based on sample size
        if context.sample_size >= 50:
            context.confidence = 100.0
        elif context.sample_size >= 20:
            context.confidence = 80.0
        elif context.sample_size >= 10:
            context.confidence = 50.0
        elif context.sample_size > 0:
            context.confidence = 25.0
        
        # Analyze strategy events
        strategy_events = [e for e in events if "strategy" in e["tags"]]
        if strategy_events:
            # Extract successful patterns
            successful = [e for e in strategy_events if e["type"] == "STRATEGY_GENERATED"]
            for event in successful:
                if "pillars_count" in event["details"]:
                    # Could extract pillar names if available
                    pass
        
        # Analyze creatives events
        creative_events = [e for e in events if "creatives" in e["tags"]]
        
        # Analyze execution events
        execution_events = [e for e in events if "execution" in e["tags"]]
        success_count = len([e for e in execution_events if event.get("details", {}).get("success")])
        if execution_events:
            success_rate = success_count / len(execution_events)
            # If success rate is high, recommend similar patterns
            if success_rate > 0.8:
                context.recommended_tones.append("current_approach_working")
        
        return context
    
    def build_context_for_segment(
        self,
        segment_id: Optional[str] = None,
        industry: Optional[str] = None,
        client_type: Optional[str] = None
    ) -> KaizenContext:
        """
        Build Kaizen context for a client segment or ICP.
        
        Analyzes events across multiple projects in this segment
        to identify patterns.
        
        Args:
            segment_id: Optional segment identifier
            industry: Optional industry filter
            client_type: Optional client type filter
            
        Returns:
            KaizenContext with segment-specific insights
        """
        # Query all events, then filter by segment characteristics
        all_events = self._query_events(days_back=180)
        
        # Filter events by segment characteristics
        segment_events = []
        for event in all_events:
            details = event.get("details", {})
            
            # Match by industry
            if industry and details.get("industry") == industry:
                segment_events.append(event)
                continue
            
            # Match by client type
            if client_type and details.get("client_segment") == client_type:
                segment_events.append(event)
                continue
            
            # Match by segment_id if provided
            if segment_id and details.get("segment_id") == segment_id:
                segment_events.append(event)
        
        context = KaizenContext()
        context.sample_size = len(segment_events)
        
        # Calculate confidence
        if context.sample_size >= 100:
            context.confidence = 100.0
        elif context.sample_size >= 50:
            context.confidence = 90.0
        elif context.sample_size >= 20:
            context.confidence = 70.0
        elif context.sample_size >= 10:
            context.confidence = 40.0
        else:
            context.confidence = 20.0
        
        # Analyze intake clarity patterns
        intake_events = [e for e in segment_events if "intake" in e["tags"]]
        if intake_events:
            clarity_scores = [
                e["details"].get("clarity_score", 50)
                for e in intake_events
                if "clarity_score" in e["details"]
            ]
            if clarity_scores:
                avg_clarity = sum(clarity_scores) / len(clarity_scores)
                if avg_clarity >= 75:
                    context.high_clarity_segments.append(industry or client_type or "unknown")
                elif avg_clarity < 50:
                    context.problematic_segments.append(industry or client_type or "unknown")
        
        # Analyze pack performance by segment
        pack_events = [e for e in segment_events if "pack" in e["tags"]]
        pack_outcomes = {}
        for event in pack_events:
            pack_key = event["details"].get("pack_key")
            if not pack_key:
                continue
            
            if pack_key not in pack_outcomes:
                pack_outcomes[pack_key] = {"total": 0, "success": 0}
            
            pack_outcomes[pack_key]["total"] += 1
            if event["type"] == "PACK_COMPLETED":
                pack_outcomes[pack_key]["success"] += 1
        
        for pack_key, outcomes in pack_outcomes.items():
            if outcomes["total"] >= 5:  # Minimum sample size
                success_rate = outcomes["success"] / outcomes["total"]
                context.pack_success_rates[pack_key] = success_rate
        
        # Analyze channel effectiveness
        execution_events = [e for e in segment_events if "execution" in e["tags"]]
        channel_stats = {}
        for event in execution_events:
            platform = event["details"].get("platform")
            if not platform:
                continue
            
            if platform not in channel_stats:
                channel_stats[platform] = {"total": 0, "success": 0}
            
            channel_stats[platform]["total"] += 1
            if event["details"].get("success"):
                channel_stats[platform]["success"] += 1
        
        for platform, stats in channel_stats.items():
            if stats["total"] >= 10:  # Minimum sample size
                effectiveness = stats["success"] / stats["total"]
                context.channel_performance[platform] = effectiveness
                
                # Add to preferred platforms if highly effective
                if effectiveness > 0.85:
                    context.preferred_platforms.append(platform)
        
        return context
    
    def get_win_rates(
        self,
        groupby: str = "pack_key",
        days_back: int = 90
    ) -> Dict[str, float]:
        """
        Calculate win rates for different dimensions.
        
        Args:
            groupby: Dimension to group by ("pack_key", "industry", "channel")
            days_back: Days back to analyze
            
        Returns:
            Dict mapping dimension values to win rates
        """
        events = self._query_events(days_back=days_back)
        
        groups = {}
        for event in events:
            details = event.get("details", {})
            group_value = details.get(groupby)
            
            if not group_value:
                continue
            
            if group_value not in groups:
                groups[group_value] = {"total": 0, "wins": 0}
            
            groups[group_value]["total"] += 1
            
            # Count wins based on event type
            if event["type"] in ["PACK_COMPLETED", "STRATEGY_GENERATED", "DEAL_WON"]:
                groups[group_value]["wins"] += 1
        
        win_rates = {}
        for group_value, stats in groups.items():
            if stats["total"] >= 5:  # Minimum sample size
                win_rates[group_value] = stats["wins"] / stats["total"]
        
        return win_rates
    
    def get_top_performing_patterns(
        self,
        pattern_type: str = "hooks",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top performing content patterns.
        
        Args:
            pattern_type: Type of pattern ("hooks", "tones", "formats")
            limit: Maximum number to return
            
        Returns:
            List of top patterns with performance metrics
        """
        # This would be more sophisticated with actual performance data
        # For now, return stub showing structure
        
        return [
            {
                "pattern": "question_hook",
                "performance_score": 0.87,
                "sample_size": 45,
                "example": "What if..."
            },
            {
                "pattern": "stat_opener",
                "performance_score": 0.82,
                "sample_size": 38,
                "example": "75% of marketers..."
            }
        ][:limit]
