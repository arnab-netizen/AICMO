from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

from aicmo.domain.state_machine import ProjectState


class ArtifactType(str, Enum):
    INTAKE = "INTAKE"
    STRATEGY = "STRATEGY"
    CREATIVES = "CREATIVES"
    EXECUTION = "EXECUTION"
    MONITORING = "MONITORING"
    DELIVERY = "DELIVERY"
    QC = "QC"


class ArtifactStatus(str, Enum):
    DRAFT = "DRAFT"
    REVISED = "REVISED"
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    ARCHIVED = "ARCHIVED"


class QualityContract(BaseModel):
    artifact_type: str
    required_depth: int
    required_specificity: int
    required_metrics: Dict[str, Any]
    anti_generic_score: float
    passes_semantic_qc: bool
    
    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

    def copy(self, *args, **kwargs):
        return self.model_copy(*args, **kwargs)


class Artifact(BaseModel):
    # Mandatory fields
    id: str
    tenant_id: str
    project_id: str
    type: ArtifactType
    status: ArtifactStatus
    schema_version: str
    version: int
    produced_by: str
    produced_at: str
    input_artifact_ids: List[str]
    state_at_creation: ProjectState
    trace_id: str
    created_by: Literal["system", "operator", "client"]
    checksum: str
    quality_contract: QualityContract
    content: Dict[str, Any]

    model_config = ConfigDict()

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

    def copy(self, *args, **kwargs):
        return self.model_copy(*args, **kwargs)

    def immutable_fields(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'checksum': self.checksum,
            'schema_version': self.schema_version,
            'input_artifact_ids': list(self.input_artifact_ids),
        }
