"""
Quality Control Models for AICMO

Defines the QC artifact schema and related enums for enforcing
minimum output quality, correctness, and usability for all client-facing artifacts.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
from datetime import datetime


class QCStatus(str, Enum):
    """QC overall status"""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class QCType(str, Enum):
    """QC artifact types matching target artifact types"""
    INTAKE_QC = "intake_qc"
    STRATEGY_QC = "strategy_qc"
    CREATIVES_QC = "creatives_qc"
    EXECUTION_QC = "execution_qc"
    MONITORING_QC = "monitoring_qc"
    DELIVERY_QC = "delivery_qc"


class CheckStatus(str, Enum):
    """Individual check status"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


class CheckSeverity(str, Enum):
    """Check severity levels"""
    BLOCKER = "BLOCKER"  # Hard blocks approval
    MAJOR = "MAJOR"      # Serious issue but may warn
    MINOR = "MINOR"      # Nice to fix


class CheckType(str, Enum):
    """Check implementation type"""
    DETERMINISTIC = "deterministic"  # Code-based validation
    LLM = "llm"                     # LLM-assisted review


@dataclass
class QCCheck:
    """Individual quality check result"""
    check_id: str
    check_type: CheckType
    status: CheckStatus
    severity: CheckSeverity
    message: str
    evidence: Optional[str] = None
    auto_fixable: bool = False
    fix_instruction: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "check_id": self.check_id,
            "check_type": self.check_type.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "evidence": self.evidence,
            "auto_fixable": self.auto_fixable,
            "fix_instruction": self.fix_instruction
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QCCheck':
        """Create from dict"""
        return cls(
            check_id=data["check_id"],
            check_type=CheckType(data["check_type"]),
            status=CheckStatus(data["status"]),
            severity=CheckSeverity(data["severity"]),
            message=data["message"],
            evidence=data.get("evidence"),
            auto_fixable=data.get("auto_fixable", False),
            fix_instruction=data.get("fix_instruction")
        )


@dataclass
class QCSummary:
    """Summary of QC check results"""
    blockers: int = 0
    majors: int = 0
    minors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QCSummary':
        """Create from dict"""
        return cls(
            blockers=data.get("blockers", 0),
            majors=data.get("majors", 0),
            minors=data.get("minors", 0)
        )


@dataclass
class QCArtifact:
    """
    Quality Control artifact for validating target artifacts.
    
    Rules:
        - Any BLOCKER check with FAIL status → qc_status = FAIL
        - qc_status = FAIL → approval blocked
        - QC artifact must be regenerated when target artifact version changes
    """
    qc_artifact_id: str
    qc_type: QCType
    target_artifact_id: str
    target_artifact_type: str
    target_version: int
    
    qc_status: QCStatus
    qc_score: int  # 0-100
    
    checks: List[QCCheck] = field(default_factory=list)
    summary: QCSummary = field(default_factory=QCSummary)
    
    model_used: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "qc_artifact_id": self.qc_artifact_id,
            "qc_type": self.qc_type.value,
            "target_artifact_id": self.target_artifact_id,
            "target_artifact_type": self.target_artifact_type,
            "target_version": self.target_version,
            "qc_status": self.qc_status.value,
            "qc_score": self.qc_score,
            "checks": [c.to_dict() for c in self.checks],
            "summary": self.summary.to_dict(),
            "model_used": self.model_used,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QCArtifact':
        """Create from dict"""
        return cls(
            qc_artifact_id=data["qc_artifact_id"],
            qc_type=QCType(data["qc_type"]),
            target_artifact_id=data["target_artifact_id"],
            target_artifact_type=data["target_artifact_type"],
            target_version=data["target_version"],
            qc_status=QCStatus(data["qc_status"]),
            qc_score=data["qc_score"],
            checks=[QCCheck.from_dict(c) for c in data.get("checks", [])],
            summary=QCSummary.from_dict(data.get("summary", {})),
            model_used=data.get("model_used"),
            created_at=data["created_at"]
        )
    
    def compute_status_and_summary(self) -> None:
        """
        Compute overall status and summary from checks.
        
        Rules:
            - Any BLOCKER with FAIL → qc_status = FAIL
            - All checks PASS → qc_status = PASS
            - Otherwise → qc_status = WARN
        """
        blockers = 0
        majors = 0
        minors = 0
        has_blocker_fail = False
        
        for check in self.checks:
            if check.severity == CheckSeverity.BLOCKER:
                blockers += 1
                if check.status == CheckStatus.FAIL:
                    has_blocker_fail = True
            elif check.severity == CheckSeverity.MAJOR:
                majors += 1
            elif check.severity == CheckSeverity.MINOR:
                minors += 1
        
        self.summary = QCSummary(blockers=blockers, majors=majors, minors=minors)
        
        if has_blocker_fail:
            self.qc_status = QCStatus.FAIL
        elif any(c.status == CheckStatus.FAIL or c.status == CheckStatus.WARN for c in self.checks):
            self.qc_status = QCStatus.WARN
        else:
            self.qc_status = QCStatus.PASS
    
    def compute_score(self) -> None:
        """
        Compute QC score (0-100) based on check results.
        
        Scoring:
            - Start at 100
            - BLOCKER FAIL: -30 points each
            - MAJOR FAIL: -10 points each
            - MINOR FAIL: -3 points each
            - WARN: -5 points each
            - Floor at 0
        """
        score = 100
        
        for check in self.checks:
            if check.status == CheckStatus.FAIL:
                if check.severity == CheckSeverity.BLOCKER:
                    score -= 30
                elif check.severity == CheckSeverity.MAJOR:
                    score -= 10
                elif check.severity == CheckSeverity.MINOR:
                    score -= 3
            elif check.status == CheckStatus.WARN:
                score -= 5
        
        self.qc_score = max(0, score)
