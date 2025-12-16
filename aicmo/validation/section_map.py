"""
Section Map Generator

Generates structured section maps for client-facing outputs at generation time.
This is the source of truth for content validation - not text extraction.
"""

import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class SectionInfo:
    """Information about a single section in a document."""
    section_id: str
    section_title: str
    word_count: int
    character_count: int
    content_hash: str
    section_order: int
    subsections: List[str]  # IDs of child sections
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SectionMap:
    """Complete section map for a document."""
    document_id: str
    document_type: str
    generation_timestamp: str
    total_word_count: int
    total_section_count: int
    sections: List[SectionInfo]
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'sections': [s.to_dict() for s in self.sections]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, filepath: str) -> None:
        """Save section map to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())


class SectionMapGenerator:
    """Generates section maps for documents."""
    
    @staticmethod
    def generate_section_id(title: str, order: int) -> str:
        """Generate stable section ID from title and order."""
        # Normalize title to lowercase, remove special chars
        normalized = ''.join(c if c.isalnum() or c.isspace() else '' 
                           for c in title.lower())
        normalized = '_'.join(normalized.split())
        return f"{normalized}_{order}"
    
    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """Calculate SHA256 hash of section content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def create_section_info(
        self,
        title: str,
        content: str,
        order: int,
        subsections: Optional[List[str]] = None
    ) -> SectionInfo:
        """Create section info from title and content."""
        section_id = self.generate_section_id(title, order)
        word_count = self.count_words(content)
        char_count = len(content)
        content_hash = self.calculate_content_hash(content)
        
        return SectionInfo(
            section_id=section_id,
            section_title=title,
            word_count=word_count,
            character_count=char_count,
            content_hash=content_hash,
            section_order=order,
            subsections=subsections or []
        )
    
    def create_section_map(
        self,
        document_id: str,
        document_type: str,
        sections: List[SectionInfo],
        metadata: Optional[Dict] = None
    ) -> SectionMap:
        """Create complete section map for a document."""
        total_words = sum(s.word_count for s in sections)
        
        return SectionMap(
            document_id=document_id,
            document_type=document_type,
            generation_timestamp=datetime.utcnow().isoformat(),
            total_word_count=total_words,
            total_section_count=len(sections),
            sections=sections,
            metadata=metadata or {}
        )
    
    def create_from_dict(
        self,
        document_id: str,
        document_type: str,
        sections_dict: Dict[str, str],
        metadata: Optional[Dict] = None
    ) -> SectionMap:
        """
        Create section map from a dictionary of section_title: content.
        
        Args:
            document_id: Unique document identifier
            document_type: Type of document (pdf, docx, etc.)
            sections_dict: Dict mapping section titles to content
            metadata: Optional metadata
            
        Returns:
            Complete SectionMap
        """
        sections = []
        for order, (title, content) in enumerate(sections_dict.items(), start=1):
            section_info = self.create_section_info(title, content, order)
            sections.append(section_info)
        
        return self.create_section_map(
            document_id=document_id,
            document_type=document_type,
            sections=sections,
            metadata=metadata
        )


# Example usage for generators
def example_report_generation():
    """Example of how to use SectionMapGenerator in a report generator."""
    generator = SectionMapGenerator()
    
    # During report generation, build sections
    sections_content = {
        "Executive Summary": "This report presents...",
        "Market Analysis": "The current market shows...",
        "Strategic Recommendations": "We recommend the following...",
        # ... more sections
    }
    
    # Create section map
    section_map = generator.create_from_dict(
        document_id="report_client123_20251215",
        document_type="marketing_strategy_report_pdf",
        sections_dict=sections_content,
        metadata={
            "client_id": "client123",
            "generated_by": "aicmo.generators.report_generator",
            "schema_version": "1.0.0"
        }
    )
    
    # Save section map alongside the PDF
    section_map.save("artifacts/report_client123_20251215.section_map.json")
    
    # Also embed reference in artifact manifest
    return section_map
