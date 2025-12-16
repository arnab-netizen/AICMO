"""
QC module database models.

Tables:
- qc_results: Main QC evaluation results
- qc_issues: Quality issues found during evaluation (1:N with results)

No foreign keys to other modules (draft_id is String, logical reference only).
"""

from sqlalchemy import Column, String, Boolean, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.base import Base


class QcResultDB(Base):
    """QC evaluation result model."""
    
    __tablename__ = "qc_results"
    
    # Primary key
    id = Column(String, primary_key=True)  # result_id (QcResultId)
    
    # Logical reference (NO FK to production module)
    draft_id = Column(String, nullable=False, unique=True, index=True)  # Idempotency key
    
    # Evaluation results
    passed = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship to issues (cascade delete)
    issues = relationship("QcIssueDB", back_populates="result", cascade="all, delete-orphan")


class QcIssueDB(Base):
    """QC quality issue model."""
    
    __tablename__ = "qc_issues"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to parent result (module-internal FK only)
    result_id = Column(String, ForeignKey("qc_results.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Issue details
    severity = Column(String, nullable=False)  # "critical", "major", "minor"
    section = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship to parent
    result = relationship("QcResultDB", back_populates="issues")
