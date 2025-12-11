"""
BrandBrainRepository: Persistent storage for brand memories.

Storage backends supported:
- SQLite (default, single-file, no setup required)
- Future: PostgreSQL, DynamoDB

Features:
- ACID guarantees
- Indexed queries for fast retrieval
- Automatic memory expiration (old, low-confidence memories)
- Semantic search (embeddings-based, optional)
"""

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from aicmo.brand.memory import BrandMemory, BrandGenerationRecord, BrandGenerationInsight

logger = logging.getLogger(__name__)


class BrandBrainRepository:
    """
    Persistent storage for BrandMemory objects.
    
    Uses SQLite by default. Manages:
    - Brand records (brand_id, name, metadata)
    - Generation records (what was generated, when, quality)
    - Insights (what we learned from generations)
    - Embeddings (for semantic search, optional)
    """
    
    def __init__(self, db_path: str = "aicmo_brand_memory.db"):
        """Initialize repository with SQLite database."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS brands (
                    brand_id TEXT PRIMARY KEY,
                    brand_name TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    total_generations INTEGER DEFAULT 0,
                    avg_generation_quality REAL DEFAULT 0.0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generation_records (
                    generation_id TEXT PRIMARY KEY,
                    brand_id TEXT NOT NULL,
                    generator_type TEXT NOT NULL,
                    brief_id TEXT,
                    prompt TEXT,
                    brief_summary TEXT,
                    output_json TEXT NOT NULL,
                    llm_provider TEXT,
                    completion_time_ms REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    confidence_score REAL DEFAULT 0.7,
                    FOREIGN KEY(brand_id) REFERENCES brands(brand_id)
                )
            """)
            
            # Create indexes separately
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_brand_id ON generation_records(brand_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_type ON generation_records(generator_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_created ON generation_records(created_at)")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation_id TEXT,
                    brand_id TEXT NOT NULL,
                    insight_text TEXT NOT NULL,
                    confidence REAL,
                    frequency INTEGER DEFAULT 1,
                    last_seen TEXT,
                    source_context TEXT,
                    generator_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(generation_id) REFERENCES generation_records(generation_id),
                    FOREIGN KEY(brand_id) REFERENCES brands(brand_id)
                )
            """)
            
            # Create indexes for insights
            conn.execute("CREATE INDEX IF NOT EXISTS idx_insight_brand_id ON insights(brand_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_insight_gen_type ON insights(generator_type)")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS brand_metadata (
                    brand_id TEXT PRIMARY KEY,
                    brand_voice_summary TEXT,
                    learned_behaviors TEXT,
                    anti_patterns TEXT,
                    learned_audience_segments TEXT,
                    resonant_topics TEXT,
                    FOREIGN KEY(brand_id) REFERENCES brands(brand_id)
                )
            """)
            
            conn.commit()
    
    def save_memory(self, memory: BrandMemory) -> None:
        """Save a complete BrandMemory to persistent storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Save brand record
                conn.execute("""
                    INSERT OR REPLACE INTO brands
                    (brand_id, brand_name, updated_at, total_generations, avg_generation_quality)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    memory.brand_id,
                    memory.brand_name,
                    memory.updated_at.isoformat(),
                    memory.total_generations,
                    memory.avg_generation_quality,
                ))
                
                # Save generation records
                for record in memory.generation_history:
                    self._save_generation_record(conn, record)
                
                # Save metadata
                conn.execute("""
                    INSERT OR REPLACE INTO brand_metadata
                    (brand_id, brand_voice_summary, learned_behaviors, anti_patterns,
                     learned_audience_segments, resonant_topics)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    memory.brand_id,
                    memory.brand_voice_summary,
                    json.dumps(memory.learned_behaviors),
                    json.dumps(memory.anti_patterns),
                    json.dumps(memory.learned_audience_segments),
                    json.dumps(memory.resonant_topics),
                ))
                
                conn.commit()
                logger.info(f"Saved memory for brand {memory.brand_id}")
        except Exception as e:
            logger.error(f"Error saving memory for brand {memory.brand_id}: {e}")
            raise
    
    def _save_generation_record(self, conn: sqlite3.Connection, record: BrandGenerationRecord) -> None:
        """Save a single generation record to the database."""
        conn.execute("""
            INSERT OR REPLACE INTO generation_records
            (generation_id, brand_id, generator_type, brief_id, prompt, brief_summary,
             output_json, llm_provider, completion_time_ms, created_at, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.generation_id,
            record.brand_id,
            record.generator_type,
            record.brief_id,
            record.prompt,
            record.brief_summary,
            json.dumps(record.output_json),
            record.llm_provider,
            record.completion_time_ms,
            record.created_at.isoformat(),
            record.confidence_score,
        ))
        
        # Save all insights
        all_insights = record.extracted_insights + record.manual_insights
        for insight in all_insights:
            conn.execute("""
                INSERT INTO insights
                (generation_id, brand_id, insight_text, confidence, frequency,
                 last_seen, source_context, generator_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.generation_id,
                record.brand_id,
                insight.insight_text,
                insight.confidence,
                insight.frequency,
                insight.last_seen.isoformat(),
                insight.source_context,
                insight.generator_type,
            ))
    
    def load_memory(self, brand_id: str) -> Optional[BrandMemory]:
        """Load a complete BrandMemory from persistent storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Load brand record
                brand_row = conn.execute(
                    "SELECT * FROM brands WHERE brand_id = ?",
                    (brand_id,)
                ).fetchone()
                
                if not brand_row:
                    logger.warning(f"Brand {brand_id} not found in database")
                    return None
                
                # Load generation records
                gen_rows = conn.execute(
                    "SELECT * FROM generation_records WHERE brand_id = ? ORDER BY created_at DESC",
                    (brand_id,)
                ).fetchall()
                
                generation_records = []
                for row in gen_rows:
                    record = BrandGenerationRecord(
                        generation_id=row["generation_id"],
                        generator_type=row["generator_type"],
                        brand_id=row["brand_id"],
                        brief_id=row["brief_id"],
                        prompt=row["prompt"],
                        brief_summary=row["brief_summary"],
                        output_json=json.loads(row["output_json"]),
                        llm_provider=row["llm_provider"],
                        completion_time_ms=row["completion_time_ms"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        confidence_score=row["confidence_score"],
                    )
                    
                    # Load insights for this record
                    insight_rows = conn.execute(
                        "SELECT * FROM insights WHERE generation_id = ?",
                        (row["generation_id"],)
                    ).fetchall()
                    
                    for irow in insight_rows:
                        insight = BrandGenerationInsight(
                            insight_text=irow["insight_text"],
                            confidence=irow["confidence"],
                            frequency=irow["frequency"],
                            last_seen=datetime.fromisoformat(irow["last_seen"]),
                            source_context=irow["source_context"],
                            generator_type=irow["generator_type"],
                        )
                        record.extracted_insights.append(insight)
                    
                    generation_records.append(record)
                
                # Load metadata
                meta_row = conn.execute(
                    "SELECT * FROM brand_metadata WHERE brand_id = ?",
                    (brand_id,)
                ).fetchone()
                
                # Create BrandMemory
                memory = BrandMemory(
                    brand_id=brand_id,
                    brand_name=brand_row["brand_name"],
                    generation_history=generation_records,
                    total_generations=brand_row["total_generations"],
                    avg_generation_quality=brand_row["avg_generation_quality"],
                    updated_at=datetime.fromisoformat(brand_row["updated_at"]),
                )
                
                if meta_row:
                    memory.brand_voice_summary = meta_row["brand_voice_summary"]
                    memory.learned_behaviors = json.loads(meta_row["learned_behaviors"] or "[]")
                    memory.anti_patterns = json.loads(meta_row["anti_patterns"] or "[]")
                    memory.learned_audience_segments = json.loads(meta_row["learned_audience_segments"] or "[]")
                    memory.resonant_topics = json.loads(meta_row["resonant_topics"] or "[]")
                
                logger.info(f"Loaded memory for brand {brand_id} with {len(generation_records)} records")
                return memory
        
        except Exception as e:
            logger.error(f"Error loading memory for brand {brand_id}: {e}")
            raise
    
    def get_recent_insights(self, brand_id: str, days: int = 30, limit: int = 10) -> List[BrandGenerationInsight]:
        """Get the most recent high-confidence insights for a brand."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT insight_text, confidence, frequency, last_seen, source_context, generator_type
                FROM insights
                WHERE brand_id = ? AND last_seen > ?
                ORDER BY (confidence * frequency) DESC
                LIMIT ?
            """, (brand_id, cutoff_date, limit)).fetchall()
        
        return [
            BrandGenerationInsight(
                insight_text=row["insight_text"],
                confidence=row["confidence"],
                frequency=row["frequency"],
                last_seen=datetime.fromisoformat(row["last_seen"]),
                source_context=row["source_context"],
                generator_type=row["generator_type"],
            )
            for row in rows
        ]
    
    def cleanup_old_memories(self, days: int = 365) -> None:
        """Remove generation records older than X days with low confidence."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Delete insights from old records
            conn.execute("""
                DELETE FROM insights
                WHERE generation_id IN (
                    SELECT generation_id FROM generation_records
                    WHERE created_at < ? AND confidence_score < 0.5
                )
            """, (cutoff_date,))
            
            # Delete old records
            conn.execute("""
                DELETE FROM generation_records
                WHERE created_at < ? AND confidence_score < 0.5
            """, (cutoff_date,))
            
            conn.commit()
            logger.info(f"Cleaned up old memories before {cutoff_date}")
    
    def list_brands(self) -> List[Dict[str, Any]]:
        """List all brands in the repository."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT brand_id, brand_name, total_generations, avg_generation_quality, updated_at FROM brands"
            ).fetchall()
        
        return [dict(row) for row in rows]
