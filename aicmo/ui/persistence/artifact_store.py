"""
Artifact-Based Dependency System for AICMO Operator

Implements versioned, gated artifacts with draft/revise/approve workflow.
All downstream modules depend on approved upstream artifacts.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict


# ===================================================================
# EXCEPTIONS
# ===================================================================

class ArtifactStateError(Exception):
    """Raised when an invalid status transition is attempted"""
    pass


class ArtifactValidationError(Exception):
    """Raised when artifact validation fails"""
    def __init__(self, errors: List[str], warnings: List[str]):
        self.errors = errors
        self.warnings = warnings
        super().__init__(f"Validation failed: {', '.join(errors)}")


class ArtifactType(str, Enum):
    """Artifact types matching operator workflow"""
    INTAKE = "intake"
    STRATEGY = "strategy"
    CREATIVES = "creatives"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    DELIVERY = "delivery"
    CAMPAIGN = "campaign"
    LEADGEN_REQUIREMENTS = "leadgen_requirements"


class ArtifactStatus(str, Enum):
    """Artifact lifecycle status"""
    DRAFT = "draft"
    REVISED = "revised"
    APPROVED = "approved"
    FLAGGED_FOR_REVIEW = "flagged_for_review"
    ARCHIVED = "archived"


@dataclass
class Artifact:
    """
    Canonical artifact model with versioning and gating.
    
    All modules produce artifacts. Downstream modules depend on approved upstream artifacts.
    When upstream changes, downstream artifacts are flagged for review.
    """
    artifact_id: str
    client_id: str
    engagement_id: str
    artifact_type: ArtifactType
    version: int
    status: ArtifactStatus
    created_at: str
    updated_at: str
    
    # Approval tracking
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    
    # Version control & stale detection
    inputs_hash: str = ""  # SHA256 of upstream artifact IDs + versions + inputs
    source_versions: Dict[str, int] = field(default_factory=dict)  # LEGACY: {artifact_type: version}
    source_lineage: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # {artifact_type: {approved_version, approved_at, artifact_id}}
    
    # Content & metadata
    content: Dict[str, Any] = field(default_factory=dict)
    notes: Dict[str, Any] = field(default_factory=dict)  # Operator notes, revision requests
    
    # Generation plan (for Intake only)
    generation_plan: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Artifact':
        """Create from dict with backward compatibility for source_lineage"""
        # Convert string enums
        if isinstance(data.get('artifact_type'), str):
            data['artifact_type'] = ArtifactType(data['artifact_type'])
        if isinstance(data.get('status'), str):
            data['status'] = ArtifactStatus(data['status'])
        
        # Backward compatibility: migrate source_versions to source_lineage
        if 'source_lineage' not in data and 'source_versions' in data:
            source_lineage = {}
            for artifact_type, version in data['source_versions'].items():
                source_lineage[artifact_type] = {
                    'approved_version': version,
                    'approved_at': None,  # Unknown for legacy data
                    'artifact_id': None   # Unknown for legacy data
                }
            data['source_lineage'] = source_lineage
            if 'notes' not in data:
                data['notes'] = {}
            data['notes']['lineage_migrated'] = True
        
        return cls(**data)


class ArtifactStore:
    """
    Artifact persistence with session state and optional backend storage.
    
    Modes:
    - inmemory: Store in session_state only
    - db: Also persist to backend (not implemented yet)
    """
    
    def __init__(self, session_state: Dict[str, Any], mode: str = "inmemory"):
        self.session_state = session_state
        self.mode = mode
        
        # Initialize artifact storage in session
        if "_artifacts" not in session_state:
            session_state["_artifacts"] = {}
    
    def get_latest_approved(
        self,
        client_id: str,
        engagement_id: str,
        artifact_type: ArtifactType
    ) -> Optional[Artifact]:
        """
        Get the latest approved artifact of a given type.
        
        Returns the highest version artifact with status=APPROVED, or None if none exist.
        """
        key = f"artifact_{artifact_type.value}"
        artifact_dict = self.session_state.get(key)
        
        if not artifact_dict:
            return None
        
        artifact = Artifact.from_dict(artifact_dict)
        
        # Check if it's approved and matches client/engagement
        if (artifact.status == ArtifactStatus.APPROVED and
            artifact.client_id == client_id and
            artifact.engagement_id == engagement_id):
            return artifact
        
        return None
    
    def get_current_approved_version_map(
        self,
        client_id: str,
        engagement_id: str
    ) -> Dict[str, Optional[int]]:
        """
        Get map of current approved versions for all artifact types.
        
        Returns: {artifact_type: approved_version or None}
        """
        version_map = {}
        
        for artifact_type in ArtifactType:
            approved = self.get_latest_approved(client_id, engagement_id, artifact_type)
            version_map[artifact_type.value] = approved.version if approved else None
        
        return version_map
    
    def _validate_status_transition(self, current: ArtifactStatus, new: ArtifactStatus) -> None:
        """
        Enforce allowed status transitions.
        
        Allowed transitions:
        - draft -> approved
        - draft -> revised
        - revised -> approved
        - approved -> flagged_for_review (cascade only)
        - approved -> archived
        - flagged_for_review -> revised
        - flagged_for_review -> approved
        
        Raises ArtifactStateError if transition is invalid.
        """
        allowed_transitions = {
            ArtifactStatus.DRAFT: [ArtifactStatus.APPROVED, ArtifactStatus.REVISED],
            ArtifactStatus.REVISED: [ArtifactStatus.APPROVED],
            ArtifactStatus.APPROVED: [ArtifactStatus.FLAGGED_FOR_REVIEW, ArtifactStatus.ARCHIVED, ArtifactStatus.REVISED],  # Allow re-revision
            ArtifactStatus.FLAGGED_FOR_REVIEW: [ArtifactStatus.REVISED, ArtifactStatus.APPROVED],
            ArtifactStatus.ARCHIVED: [],
        }
        
        valid_next = allowed_transitions.get(current, [])
        if new not in valid_next:
            raise ArtifactStateError(
                f"Invalid status transition: {current.value} -> {new.value}. "
                f"Allowed transitions from {current.value}: {[s.value for s in valid_next]}"
            )
    
    def create_artifact(
        self,
        artifact_type: ArtifactType,
        client_id: str,
        engagement_id: str,
        content: Dict[str, Any],
        source_artifacts: Optional[List[Artifact]] = None,
        generation_plan: Optional[Dict[str, Any]] = None
    ) -> Artifact:
        """Create a new artifact (version 1, draft status)"""
        now_iso = datetime.utcnow().isoformat()
        
        # Compute inputs hash from source artifacts
        inputs_hash = self._compute_inputs_hash(source_artifacts, content)
        
        # Extract source versions (LEGACY - keep for backward compat)
        source_versions = {}
        if source_artifacts:
            for source in source_artifacts:
                source_versions[source.artifact_type.value] = source.version
        
        # Build source_lineage from APPROVED upstream artifacts
        source_lineage = {}
        if source_artifacts:
            for source in source_artifacts:
                # Only record lineage if source is approved
                if source.status == ArtifactStatus.APPROVED:
                    source_lineage[source.artifact_type.value] = {
                        'approved_version': source.version,
                        'approved_at': source.approved_at,
                        'artifact_id': source.artifact_id
                    }
        
        artifact = Artifact(
            artifact_id=str(uuid.uuid4()),
            client_id=client_id,
            engagement_id=engagement_id,
            artifact_type=artifact_type,
            version=1,
            status=ArtifactStatus.DRAFT,
            created_at=now_iso,
            updated_at=now_iso,
            inputs_hash=inputs_hash,
            source_versions=source_versions,
            source_lineage=source_lineage,
            content=content,
            generation_plan=generation_plan
        )
        
        # Store in session
        key = f"artifact_{artifact_type.value}"
        self.session_state[key] = artifact.to_dict()
        self.session_state["_artifacts"][artifact.artifact_id] = artifact.to_dict()
        
        return artifact
    
    def update_artifact(
        self,
        artifact: Artifact,
        content: Dict[str, Any],
        notes: Optional[Dict[str, Any]] = None,
        increment_version: bool = True
    ) -> Artifact:
        """
        Update existing artifact (revision workflow).
        
        NOTE: Cascade is NOT triggered here. Cascade only triggers when an artifact
        is approved with a new approved version (see approve_artifact).
        """
        now_iso = datetime.utcnow().isoformat()
        
        # Only increment version if content actually changed
        content_changed = (artifact.content != content)
        
        if increment_version and content_changed:
            artifact.version += 1
            # Validate status transition
            self._validate_status_transition(artifact.status, ArtifactStatus.REVISED)
            artifact.status = ArtifactStatus.REVISED
        
        artifact.content = content
        artifact.updated_at = now_iso
        
        if notes:
            artifact.notes.update(notes)
        
        # Update storage
        key = f"artifact_{artifact.artifact_type.value}"
        self.session_state[key] = artifact.to_dict()
        self.session_state["_artifacts"][artifact.artifact_id] = artifact.to_dict()
        
        return artifact
    
    def approve_artifact(
        self,
        artifact: Artifact,
        approved_by: str = "operator",
        approval_note: Optional[str] = None
    ) -> Artifact:
        """
        Approve artifact with strict validation enforcement.
        
        This is the ONLY valid approval path. UI must call this method.
        
        Triggers cascade if this is a new/higher approved version.
        
        Raises:
            ArtifactValidationError: If validation fails
            ArtifactStateError: If status transition is invalid
        """
        # Capture previous approved version BEFORE approval
        prev_approved = self.get_latest_approved(
            artifact.client_id,
            artifact.engagement_id,
            artifact.artifact_type
        )
        prev_approved_version = prev_approved.version if prev_approved else 0
        
        # Run validation BEFORE approval
        ok, errors, warnings = self._validate_artifact_content(artifact.artifact_type, artifact.content)
        
        if not ok:
            raise ArtifactValidationError(errors, warnings)
        
        # Validate status transition
        self._validate_status_transition(artifact.status, ArtifactStatus.APPROVED)
        
        now_iso = datetime.utcnow().isoformat()
        
        artifact.status = ArtifactStatus.APPROVED
        artifact.approved_at = now_iso
        artifact.approved_by = approved_by
        artifact.updated_at = now_iso
        
        if approval_note:
            artifact.notes["approval_note"] = approval_note
        if warnings:
            artifact.notes["approval_warnings"] = warnings
        
        # Update storage
        key = f"artifact_{artifact.artifact_type.value}"
        self.session_state[key] = artifact.to_dict()
        self.session_state["_artifacts"][artifact.artifact_id] = artifact.to_dict()
        
        # Trigger cascade if this is a NEW approved version
        if artifact.version > prev_approved_version:
            downstream_types = self._get_downstream_types(artifact.artifact_type)
            if downstream_types:
                self.cascade_on_upstream_change(artifact, downstream_types)
        
        return artifact
    
    def flag_artifact_for_review(self, artifact: Artifact, reason: str) -> Artifact:
        """Flag artifact when upstream changes (stale cascade)"""
        # Validate transition (only from approved)
        self._validate_status_transition(artifact.status, ArtifactStatus.FLAGGED_FOR_REVIEW)
        
        artifact.status = ArtifactStatus.FLAGGED_FOR_REVIEW
        artifact.updated_at = datetime.utcnow().isoformat()
        artifact.notes["flagged_reason"] = reason
        artifact.notes["flagged_at"] = artifact.updated_at
        
        # Update storage
        key = f"artifact_{artifact.artifact_type.value}"
        self.session_state[key] = artifact.to_dict()
        self.session_state["_artifacts"][artifact.artifact_id] = artifact.to_dict()
        
        return artifact
    
    def check_stale_cascade(
        self,
        upstream_artifact: Artifact,
        downstream_types: List[ArtifactType]
    ) -> List[Artifact]:
        """
        Check if downstream artifacts need to be flagged due to upstream change.
        
        Returns list of artifacts that were flagged.
        """
        flagged = []
        
        for dtype in downstream_types:
            key = f"artifact_{dtype.value}"
            downstream_dict = self.session_state.get(key)
            
            if not downstream_dict:
                continue
            
            downstream = Artifact.from_dict(downstream_dict)
            
            # Check if downstream was built on old version of upstream
            upstream_type_str = upstream_artifact.artifact_type.value
            if upstream_type_str in downstream.source_versions:
                old_version = downstream.source_versions[upstream_type_str]
                if old_version < upstream_artifact.version:
                    # Downstream is stale
                    self.flag_artifact_for_review(
                        downstream,
                        f"Upstream {upstream_type_str} changed from v{old_version} to v{upstream_artifact.version}"
                    )
                    flagged.append(downstream)
        
        return flagged
    
    def get_artifact(self, artifact_type: ArtifactType) -> Optional[Artifact]:
        """Get artifact from session by type"""
        key = f"artifact_{artifact_type.value}"
        data = self.session_state.get(key)
        if data:
            return Artifact.from_dict(data)
        return None
    
    def _validate_artifact_content(
        self,
        artifact_type: ArtifactType,
        content: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate artifact content by type.
        
        Returns: (ok: bool, errors: List[str], warnings: List[str])
        """
        if artifact_type == ArtifactType.INTAKE:
            return validate_intake_content(content)
        elif artifact_type == ArtifactType.STRATEGY:
            return validate_strategy_contract(content)
        else:
            # For now, other types have no validation
            return (True, [], [])
    
    def _get_downstream_types(self, artifact_type: ArtifactType) -> List[ArtifactType]:
        """Get list of artifact types that depend on this one"""
        downstream_map = {
            ArtifactType.INTAKE: [ArtifactType.STRATEGY],
            ArtifactType.STRATEGY: [ArtifactType.CREATIVES],  # Strategy directly flows to Creatives
            ArtifactType.CREATIVES: [ArtifactType.EXECUTION],
            ArtifactType.EXECUTION: [ArtifactType.MONITORING],
        }
        return downstream_map.get(artifact_type, [])
    
    def cascade_on_upstream_change(
        self,
        upstream_artifact: Artifact,
        downstream_types: List[ArtifactType]
    ) -> List[Artifact]:
        """
        Automatically flag downstream artifacts when upstream APPROVED version changes.
        
        Called from approve_artifact when a new approved version is created.
        
        Uses source_lineage to compare against approved versions (not draft versions).
        
        Returns: List of artifacts that were flagged.
        """
        flagged = []
        upstream_type_str = upstream_artifact.artifact_type.value
        
        for dtype in downstream_types:
            key = f"artifact_{dtype.value}"
            downstream_dict = self.session_state.get(key)
            
            if not downstream_dict:
                continue
            
            downstream = Artifact.from_dict(downstream_dict)
            
            # Only flag if downstream is currently approved
            if downstream.status != ArtifactStatus.APPROVED:
                continue
            
            # Check source_lineage for approved version tracking
            if upstream_type_str in downstream.source_lineage:
                old_approved_version = downstream.source_lineage[upstream_type_str]['approved_version']
                new_approved_version = upstream_artifact.version
                
                if old_approved_version < new_approved_version:
                    # Downstream is stale - upstream approved version advanced
                    try:
                        self.flag_artifact_for_review(
                            downstream,
                            f"Upstream {upstream_type_str} approved version changed from v{old_approved_version} to v{new_approved_version}"
                        )
                        flagged.append(downstream)
                    except ArtifactStateError:
                        # Can't flag (e.g., already flagged or in draft)
                        pass
            # Fallback to source_versions for backward compat
            elif upstream_type_str in downstream.source_versions:
                old_version = downstream.source_versions[upstream_type_str]
                if old_version < upstream_artifact.version:
                    # Downstream is stale
                    try:
                        self.flag_artifact_for_review(
                            downstream,
                            f"Upstream {upstream_type_str} changed from v{old_version} to v{upstream_artifact.version}"
                        )
                        flagged.append(downstream)
                    except ArtifactStateError:
                        # Can't flag (e.g., already flagged or in draft)
                        pass
        
        return flagged
    
    def _compute_inputs_hash(
        self,
        source_artifacts: Optional[List[Artifact]],
        content: Dict[str, Any]
    ) -> str:
        """
        Compute SHA256 hash of inputs for change detection.
        
        Uses approved lineage when available to detect approved version changes.
        """
        hash_input = {}
        
        if source_artifacts:
            for source in source_artifacts:
                # Use approved version if source is approved, otherwise use current version
                if source.status == ArtifactStatus.APPROVED:
                    hash_input[source.artifact_type.value] = {
                        "id": source.artifact_id,
                        "approved_version": source.version,
                        "approved_at": source.approved_at
                    }
                else:
                    hash_input[source.artifact_type.value] = {
                        "id": source.artifact_id,
                        "version": source.version
                    }
        
        # Add content keys (not full content to avoid noise)
        hash_input["content_keys"] = sorted(content.keys())
        
        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()


# ===================================================================
# GATING LOGIC
# ===================================================================

GATING_MAP = {
    ArtifactType.STRATEGY: [ArtifactType.INTAKE],
    ArtifactType.CREATIVES: [ArtifactType.STRATEGY],
    ArtifactType.EXECUTION: [ArtifactType.STRATEGY, ArtifactType.CREATIVES],
    ArtifactType.MONITORING: [ArtifactType.EXECUTION],
    ArtifactType.DELIVERY: [ArtifactType.INTAKE, ArtifactType.STRATEGY, ArtifactType.CREATIVES, ArtifactType.EXECUTION],
}


def check_gating(
    artifact_type: ArtifactType,
    artifact_store: ArtifactStore
) -> Tuple[bool, List[str]]:
    """
    Check if all required upstream artifacts are approved.
    
    Returns: (allowed: bool, blocking_reasons: List[str])
    """
    required_types = GATING_MAP.get(artifact_type, [])
    blocking_reasons = []
    
    for required_type in required_types:
        upstream = artifact_store.get_artifact(required_type)
        
        if not upstream:
            blocking_reasons.append(f"Missing {required_type.value} artifact")
            continue
        
        if upstream.status != ArtifactStatus.APPROVED:
            blocking_reasons.append(
                f"{required_type.value} is {upstream.status.value} (must be approved)"
            )
    
    return (len(blocking_reasons) == 0, blocking_reasons)


# ===================================================================
# VALIDATION
# ===================================================================

def validate_intake_content(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate intake content with deterministic checks.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Required fields
    required = ["client_name", "website", "industry", "geography", "primary_offer", "objective"]
    for field in required:
        if not content.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Consistency checks
    objective = content.get("objective", "")
    if objective == "Leads" and not content.get("target_audience"):
        warnings.append("Lead generation objective but no target audience specified")
    
    if objective == "Hiring" and "context_data" not in content:
        warnings.append("Hiring objective but no EVP/role context provided")
    
    # Check for contradictions
    budget_range = content.get("budget_range", "")
    if "student" in content.get("target_audience", "").lower() and "high-ticket" in budget_range.lower():
        warnings.append("Student audience with high-ticket pricing may be inconsistent")
    
    # Check generation plan consistency
    generation_plan_dict = content.get("generation_plan")
    if generation_plan_dict:
        jobs = generation_plan_dict.get("jobs", [])
        if not jobs:
            warnings.append("Generation plan exists but no jobs selected")
    
    return (len(errors) == 0, errors, warnings)


def validate_strategy_contract(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate strategy contract schema.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Required schema fields for Strategy Contract
    required_keys = [
        "icp",
        "positioning",
        "messaging",
        "content_pillars",
        "platform_plan",
        "cta_rules",
        "measurement"
    ]
    
    for key in required_keys:
        if key not in content:
            errors.append(f"Strategy contract missing required field: {key}")
    
    # Check ICP structure
    if "icp" in content:
        icp = content["icp"]
        if not isinstance(icp, dict):
            errors.append("ICP must be a structured object")
        else:
            if "segments" not in icp:
                errors.append("ICP missing 'segments' field")
    
    # Check positioning structure
    if "positioning" in content:
        pos = content["positioning"]
        if not isinstance(pos, dict):
            errors.append("Positioning must be a structured object")
        else:
            if "statement" not in pos:
                errors.append("Positioning missing 'statement' field")
    
    # Warnings for missing optional fields
    if "compliance" in content:
        compliance = content["compliance"]
        if not compliance.get("forbidden_claims") and not compliance.get("required_disclaimers"):
            warnings.append("Compliance section present but empty - verify if intentional")
    
    return (len(errors) == 0, errors, warnings)
