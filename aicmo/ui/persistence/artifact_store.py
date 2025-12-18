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

# Import canonical gating from unified module
from aicmo.ui.gating import GATING_MAP


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


class ConflictError(Exception):
    """Raised when optimistic locking detects a conflict."""
    def to_error_response(self):
        try:
            from aicmo.api.schemas import ErrorResponse
        except Exception:
            return {"error_code": "CONFLICT", "message": "Conflict", "details": None, "trace_id": ""}
        return ErrorResponse(error_code="CONFLICT", message="Version conflict", details=None, trace_id="")


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
    
    def build_source_lineage(
        self,
        client_id: str,
        engagement_id: str,
        required_types: List[ArtifactType]
    ) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        """
        Build source_lineage dict from latest approved upstream artifacts.
        
        Args:
            client_id: Client ID
            engagement_id: Engagement ID
            required_types: List of upstream artifact types that MUST be approved
        
        Returns:
            (lineage_dict, errors)
            lineage_dict: {artifact_type: {approved_version, approved_at, artifact_id}}
            errors: List of error messages (empty if all required types approved)
        """
        lineage = {}
        errors = []
        
        for artifact_type in required_types:
            approved = self.get_latest_approved(client_id, engagement_id, artifact_type)
            
            if not approved:
                errors.append(f"Required upstream {artifact_type.value} not approved")
            else:
                lineage[artifact_type.value] = {
                    'approved_version': approved.version,
                    'approved_at': approved.approved_at,
                    'artifact_id': approved.artifact_id
                }
        
        return lineage, errors
    
    def assert_lineage_fresh(
        self,
        lineage: Dict[str, Dict[str, Any]],
        client_id: str,
        engagement_id: str
    ) -> Tuple[bool, List[str]]:
        """
        Verify that lineage references are fresh (match current approved versions).
        
        Args:
            lineage: source_lineage dict from artifact
            client_id: Client ID
            engagement_id: Engagement ID
        
        Returns:
            (ok, errors)
            ok: True if all lineage refs are fresh
            errors: List of stale references (empty if fresh)
        """
        errors = []
        
        for artifact_type_str, lineage_info in lineage.items():
            try:
                artifact_type = ArtifactType(artifact_type_str)
            except ValueError:
                errors.append(f"Unknown artifact type in lineage: {artifact_type_str}")
                continue
            
            current_approved = self.get_latest_approved(client_id, engagement_id, artifact_type)
            
            if not current_approved:
                errors.append(f"Upstream {artifact_type_str} no longer approved")
                continue
            
            lineage_version = lineage_info.get('approved_version')
            if lineage_version != current_approved.version:
                errors.append(
                    f"Stale {artifact_type_str}: lineage has v{lineage_version}, "
                    f"current approved is v{current_approved.version}"
                )
        
        return (len(errors) == 0, errors)

    def validate_required_lineage(
        self,
        artifact: Artifact,
        selected_job_ids: Optional[List[str]] = None
    ) -> tuple[bool, List[str]]:
        """
        Validate that artifact has all required upstream lineage.
        
        Args:
            artifact: Artifact to validate
            selected_job_ids: Optional job IDs for execution dependency resolution
        
        Returns:
            (ok, errors)
            ok: True if all required lineage present
            errors: List of missing lineage types
        
        Rules enforced:
            - Strategy MUST have intake lineage
            - Creatives MUST have strategy lineage
            - Execution MUST have strategy lineage (+ creatives if jobs require)
            - Other types: no lineage required
        """
        from aicmo.ui.generation_plan import required_upstreams_for
        
        artifact_type_str = artifact.artifact_type.value
        required = required_upstreams_for(artifact_type_str, selected_job_ids or [])
        
        if not required:
            # No lineage required for this artifact type
            return (True, [])
        
        current_lineage = artifact.source_lineage or {}
        missing = []
        
        for required_type in required:
            if required_type not in current_lineage:
                missing.append(f"Required upstream {required_type} lineage missing")
        
        return (len(missing) == 0, missing)

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

    # --- Phase 3 required store API ---
    def put(self, artifact: Any, expected_version: Optional[int] = None) -> Dict[str, Any]:
        """Persist an artifact (domain model or dict). Enforce optimistic locking.

        If expected_version is provided and doesn't match latest, raise ConflictError.
        This method will store a new version (monotonic) rather than mutating immutable fields.
        Returns the stored artifact dict.
        """
        # Accept either domain model or dict. Prefer Pydantic v2 `model_dump` when
        # available to avoid deprecated `.dict()` usage warnings being treated
        # as errors in the test environment.
        if hasattr(artifact, "model_dump"):
            art_dict = artifact.model_dump()
        elif hasattr(artifact, "dict"):
            art_dict = artifact.dict()
        elif isinstance(artifact, dict):
            art_dict = artifact
        else:
            # Fallback: try to convert dataclass-style
            try:
                art_dict = dict(artifact)
            except Exception:
                raise ValueError("Unsupported artifact type for put()")

        tenant_id = art_dict.get("tenant_id")
        project_id = art_dict.get("project_id")
        art_type = art_dict.get("type") or art_dict.get("artifact_type")
        if isinstance(art_type, str):
            art_type_key = str(art_type)
        else:
            art_type_key = getattr(art_type, "value", str(art_type))

        # Find latest for (tenant, project, type)
        latest = self.latest(tenant_id, project_id, art_type_key)
        latest_version = latest.get("version") if latest else 0

        if expected_version is not None and expected_version != latest_version:
            raise ConflictError()

        # New version number
        new_version = latest_version + 1
        art_dict["version"] = new_version

        # Assign id if missing
        if not art_dict.get("id") and not art_dict.get("artifact_id"):
            art_dict["id"] = str(uuid.uuid4())

        # Normalize id key
        artifact_id = art_dict.get("id") or art_dict.get("artifact_id")
        # Store consistently under _artifacts
        self.session_state.setdefault("_artifacts", {})
        self.session_state["_artifacts"][artifact_id] = art_dict

        # Also store a per-project/type pointer for quick latest lookup
        key = f"artifact_{art_type_key}_{tenant_id}_{project_id}"
        self.session_state[key] = art_dict

        return art_dict

    def get(self, tenant_id: str, artifact_id: str) -> Optional[Dict[str, Any]]:
        self.session_state.setdefault("_artifacts", {})
        return self.session_state["_artifacts"].get(artifact_id)

    def list_by_project(self, tenant_id: str, project_id: str) -> List[Dict[str, Any]]:
        out = []
        for a in self.session_state.get("_artifacts", {}).values():
            if a.get("tenant_id") == tenant_id and a.get("project_id") == project_id:
                out.append(a)
        return out

    def latest(self, tenant_id: str, project_id: str, artifact_type: Any) -> Optional[Dict[str, Any]]:
        # Accept ArtifactType or str
        art_type_key = artifact_type
        if hasattr(artifact_type, "value"):
            art_type_key = artifact_type.value
        # Check per-project pointer first
        key = f"artifact_{art_type_key}_{tenant_id}_{project_id}"
        candidate = self.session_state.get(key)
        if candidate:
            return candidate
        # Fallback scan
        latest = None
        for a in self.session_state.get("_artifacts", {}).values():
            if a.get("tenant_id") == tenant_id and a.get("project_id") == project_id and (a.get("type") == art_type_key or a.get("artifact_type") == art_type_key or a.get("artifact_type") == art_type_key.lower()):
                if latest is None or a.get("version", 0) > latest.get("version", 0):
                    latest = a
        return latest
    
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
            ArtifactValidationError: If validation fails (content, lineage, or QC)
            ArtifactStateError: If status transition is invalid
        """
        # Capture previous approved version BEFORE approval
        prev_approved = self.get_latest_approved(
            artifact.client_id,
            artifact.engagement_id,
            artifact.artifact_type
        )
        prev_approved_version = prev_approved.version if prev_approved else 0
        
        # Run content validation BEFORE approval
        ok, errors, warnings = self._validate_artifact_content(artifact.artifact_type, artifact.content)
        
        if not ok:
            raise ArtifactValidationError(errors, warnings)
        
        # Validate REQUIRED lineage is present (must happen before freshness check)
        lineage_required_ok, lineage_required_errors = self.validate_required_lineage(
            artifact,
            selected_job_ids=artifact.notes.get("selected_job_ids", [])
        )
        if not lineage_required_ok:
            raise ArtifactValidationError(lineage_required_errors, [])
        
        # Validate lineage freshness if artifact has source_lineage
        if artifact.source_lineage:
            lineage_ok, lineage_errors = self.assert_lineage_fresh(
                artifact.source_lineage,
                artifact.client_id,
                artifact.engagement_id
            )
            if not lineage_ok:
                raise ArtifactValidationError(lineage_errors, [])
        
        # NEW: Enforce QC gate - no approval without passing QC
        qc_ok, qc_errors = self._check_qc_gate(artifact)
        if not qc_ok:
            raise ArtifactValidationError(qc_errors, [])
        
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
        elif artifact_type == ArtifactType.CREATIVES:
            return validate_creatives_content(content)
        elif artifact_type == ArtifactType.EXECUTION:
            return validate_execution_content(content)
        elif artifact_type == ArtifactType.MONITORING:
            return validate_monitoring_content(content)
        elif artifact_type == ArtifactType.DELIVERY:
            return validate_delivery_content(content)
        else:
            # No validation for other types
            return (True, [], [])
    
    def store_qc_artifact(self, qc_artifact) -> None:
        """Store QC artifact in session state"""
        if "_qc_artifacts" not in self.session_state:
            self.session_state["_qc_artifacts"] = {}
        
        key = f"{qc_artifact.target_artifact_id}_v{qc_artifact.target_version}"
        self.session_state["_qc_artifacts"][key] = qc_artifact.to_dict()
    
    def get_qc_for_artifact(self, artifact: Artifact):
        """
        Get QC artifact for given artifact.
        
        Returns QCArtifact or None if not found.
        """
        if "_qc_artifacts" not in self.session_state:
            return None
        
        key = f"{artifact.artifact_id}_v{artifact.version}"
        qc_data = self.session_state["_qc_artifacts"].get(key)
        
        if qc_data:
            # Import here to avoid circular dependency
            from aicmo.ui.quality.qc_models import QCArtifact
            return QCArtifact.from_dict(qc_data)
        
        return None
    
    def _check_qc_gate(self, artifact: Artifact) -> Tuple[bool, List[str]]:
        """
        Enforce QC gate: artifact cannot be approved without passing QC.
        
        Rules:
            1. QC artifact must exist for this artifact_id + version
            2. QC artifact target_version must match artifact.version
            3. QC status must not be FAIL
        
        Returns: (ok: bool, errors: List[str])
        """
        from aicmo.ui.quality.qc_models import QCStatus
        
        errors = []
        
        # Rule 1: QC must exist
        qc_artifact = self.get_qc_for_artifact(artifact)
        if not qc_artifact:
            errors.append(
                f"Cannot approve {artifact.artifact_type.value}: No QC artifact found. "
                f"Run QC checks before approval."
            )
            return (False, errors)
        
        # Rule 2: Version lock
        if qc_artifact.target_version != artifact.version:
            errors.append(
                f"QC version mismatch: QC is for version {qc_artifact.target_version}, "
                f"but artifact is version {artifact.version}. Regenerate QC."
            )
            return (False, errors)
        
        # Rule 3: QC must not have FAIL status
        if qc_artifact.qc_status == QCStatus.FAIL:
            blocker_checks = [
                check for check in qc_artifact.checks
                if check.status.value == "FAIL" and check.severity.value == "BLOCKER"
            ]
            blocker_messages = [check.message for check in blocker_checks]
            
            errors.append(
                f"QC failed with {len(blocker_checks)} blocker(s). Cannot approve."
            )
            errors.extend(blocker_messages[:3])  # Show first 3 blockers
            
            if len(blocker_messages) > 3:
                errors.append(f"... and {len(blocker_messages) - 3} more blockers")
            
            return (False, errors)
        
        # QC gate passed
        return (True, [])
    
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
# GATING_MAP imported from aicmo.ui.gating (single source of truth)


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


def validate_creatives_content(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Creatives artifact content.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Basic structure check - must have some creatives-like content
    if not content:
        errors.append("Creatives content is empty")
        return (False, errors, warnings)
    
    # Check for common creatives structures
    has_creatives_list = "creatives" in content and isinstance(content.get("creatives"), list)
    has_posts_list = "posts" in content and isinstance(content.get("posts"), list)
    has_content_field = any(k in content for k in ["content", "creative_content", "assets"])
    
    if not (has_creatives_list or has_posts_list or has_content_field):
        warnings.append("Creatives content doesn't have standard structure (creatives, posts, or assets)")
    
    return (len(errors) == 0, errors, warnings)


def validate_execution_content(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Execution artifact content.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Basic structure check
    if not content:
        errors.append("Execution content is empty")
        return (False, errors, warnings)
    
    # Check for execution-like structures
    has_schedule = "schedule" in content or "calendar" in content
    has_posts = "posts" in content
    has_timeline = "timeline" in content or "execution_plan" in content
    
    if not (has_schedule or has_posts or has_timeline):
        warnings.append("Execution content doesn't have standard structure (schedule, posts, or timeline)")
    
    return (len(errors) == 0, errors, warnings)


def validate_monitoring_content(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Monitoring artifact content.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Basic structure check
    if not content:
        errors.append("Monitoring content is empty")
        return (False, errors, warnings)
    
    # Check for KPI configuration
    if "kpi_config" in content:
        kpi_config = content["kpi_config"]
        if not kpi_config.get("selected_kpis"):
            warnings.append("No KPIs selected for monitoring")
        if not kpi_config.get("kpi_targets"):
            warnings.append("No KPI targets defined")
    else:
        warnings.append("Monitoring missing kpi_config section")
    
    # Check for tracking setup
    if "tracking" not in content:
        warnings.append("Monitoring missing tracking configuration")
    
    # Check for reporting setup
    if "reporting" not in content:
        warnings.append("Monitoring missing reporting configuration")
    
    return (len(errors) == 0, errors, warnings)


def validate_delivery_content(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Delivery artifact content.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Basic structure check
    if not content:
        errors.append("Delivery content is empty")
        return (False, errors, warnings)
    
    # Check for artifact selection
    if "artifact_selection" in content:
        artifact_selection = content["artifact_selection"]
        selected_count = sum([
            artifact_selection.get("include_intake", False),
            artifact_selection.get("include_strategy", False),
            artifact_selection.get("include_creatives", False),
            artifact_selection.get("include_execution", False),
            artifact_selection.get("include_monitoring", False)
        ])
        if selected_count == 0:
            errors.append("No artifacts selected for delivery")
    else:
        warnings.append("Delivery missing artifact_selection section")
    
    # Check for export formats
    if "export_formats" in content:
        export_formats = content["export_formats"]
        format_count = sum([
            export_formats.get("pdf", False),
            export_formats.get("pptx", False),
            export_formats.get("json", False),
            export_formats.get("zip", False)
        ])
        if format_count == 0:
            errors.append("No export formats selected")
    else:
        warnings.append("Delivery missing export_formats section")
    
    # Check pre-flight checklist
    if "checklist" in content:
        checklist = content["checklist"]
        if not checklist.get("checklist_complete", False):
            warnings.append("Pre-flight checklist not complete")
    else:
        warnings.append("Delivery missing pre-flight checklist")
    
    return (len(errors) == 0, errors, warnings)


def validate_strategy_contract(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate 8-layer strategy contract schema.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Layer 1: Business Reality Alignment
    if "layer1_business_reality" not in content:
        errors.append("Missing Layer 1: Business Reality Alignment")
    else:
        l1 = content["layer1_business_reality"]
        required_l1 = ["business_model_summary", "revenue_streams", "unit_economics", 
                       "pricing_logic", "growth_constraint", "bottleneck"]
        for field in required_l1:
            if not l1.get(field):
                errors.append(f"Layer 1 missing required field: {field}")
    
    # Layer 2: Market & Competitive Truth
    if "layer2_market_truth" not in content:
        errors.append("Missing Layer 2: Market & Competitive Truth")
    else:
        l2 = content["layer2_market_truth"]
        required_l2 = ["category_maturity", "white_space_logic", "what_not_to_do"]
        for field in required_l2:
            if not l2.get(field):
                errors.append(f"Layer 2 missing required field: {field}")
    
    # Layer 3: Audience Decision Psychology
    if "layer3_audience_psychology" not in content:
        errors.append("Missing Layer 3: Audience Decision Psychology")
    else:
        l3 = content["layer3_audience_psychology"]
        required_l3 = ["awareness_state", "objection_hierarchy", "trust_transfer_mechanism"]
        for field in required_l3:
            if not l3.get(field):
                errors.append(f"Layer 3 missing required field: {field}")
    
    # Layer 4: Value Proposition Architecture
    if "layer4_value_architecture" not in content:
        errors.append("Missing Layer 4: Value Proposition Architecture")
    else:
        l4 = content["layer4_value_architecture"]
        required_l4 = ["core_promise", "sacrifice_framing", "differentiation_logic"]
        for field in required_l4:
            if not l4.get(field):
                errors.append(f"Layer 4 missing required field: {field}")
    
    # Layer 5: Strategic Narrative
    if "layer5_narrative" not in content:
        errors.append("Missing Layer 5: Strategic Narrative")
    else:
        l5 = content["layer5_narrative"]
        required_l5 = ["narrative_problem", "narrative_tension", "narrative_resolution", 
                       "enemy_definition", "repetition_logic"]
        for field in required_l5:
            if not l5.get(field):
                errors.append(f"Layer 5 missing required field: {field}")
    
    # Layer 6: Channel Strategy
    if "layer6_channel_strategy" not in content:
        errors.append("Missing Layer 6: Channel Strategy")
    else:
        l6 = content["layer6_channel_strategy"]
        if "channels" not in l6 or not l6["channels"]:
            errors.append("Layer 6 must define at least one channel")
        else:
            for idx, channel in enumerate(l6["channels"]):
                if not channel.get("name"):
                    errors.append(f"Layer 6 channel {idx+1} missing name")
                if not channel.get("strategic_role"):
                    warnings.append(f"Layer 6 channel {idx+1} ({channel.get('name', 'unnamed')}) missing strategic role")
    
    # Layer 7: Execution Constraints
    if "layer7_constraints" not in content:
        errors.append("Missing Layer 7: Execution Constraints")
    else:
        l7 = content["layer7_constraints"]
        required_l7 = ["tone_boundaries", "forbidden_language", "claim_boundaries", "compliance_rules"]
        for field in required_l7:
            if not l7.get(field):
                errors.append(f"Layer 7 missing required field: {field}")
    
    # Layer 8: Measurement & Learning Loop
    if "layer8_measurement" not in content:
        errors.append("Missing Layer 8: Measurement & Learning Loop")
    else:
        l8 = content["layer8_measurement"]
        required_l8 = ["success_definition", "leading_indicators", "lagging_indicators", "decision_rules"]
        for field in required_l8:
            if not l8.get(field):
                errors.append(f"Layer 8 missing required field: {field}")
    
    # Warnings for common issues
    if "layer1_business_reality" in content:
        l1 = content["layer1_business_reality"]
        if l1.get("bottleneck") not in ["Demand", "Awareness", "Trust", "Conversion", "Retention", ""]:
            warnings.append("Layer 1 bottleneck should be one of: Demand, Awareness, Trust, Conversion, Retention")
    
    if "layer4_value_architecture" in content:
        l4 = content["layer4_value_architecture"]
        if l4.get("differentiation_logic") not in ["Structural", "Cosmetic", ""]:
            warnings.append("Layer 4 differentiation logic should be either Structural or Cosmetic")
    
    return (len(errors) == 0, errors, warnings)


# ===================================================================
# ALIASES & TEST HELPERS
# ===================================================================

# Alias for backward compatibility and cleaner imports
validate_intake = validate_intake_content


def normalize_intake_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize intake payload for approval validation.
    
    Mapping rules (exact per user specification):
    - client_name ← payload.get("client_name") OR payload.get("brand_name")
    - geography ← payload.get("geography") OR payload.get("geography_served")
    - primary_offer ← payload.get("primary_offer") OR payload.get("primary_offers")
    - objective ← payload.get("objective") OR payload.get("primary_objective")
    
    Preserves all other fields unchanged (website, industry, target_audience, 
    pain_points, desired_outcomes, constraints, tone_voice, proof_assets, 
    unit_economics, etc.)
    
    Args:
        payload: Raw intake dict from UI
    
    Returns:
        Normalized intake dict with canonical field names
    """
    normalized = payload.copy()
    
    # Apply mapping rules
    if "brand_name" in payload and "client_name" not in payload:
        normalized["client_name"] = payload["brand_name"]
    
    if "geography_served" in payload and "geography" not in payload:
        normalized["geography"] = payload["geography_served"]
    
    if "primary_offers" in payload and "primary_offer" not in payload:
        normalized["primary_offer"] = payload["primary_offers"]
    
    if "primary_objective" in payload and "objective" not in payload:
        normalized["objective"] = payload["primary_objective"]
    
    return normalized


def create_valid_intake_content() -> Dict[str, Any]:
    """
    Helper function for tests: creates a valid intake content dict.
    
    Returns intake content dict with all required fields populated.
    """
    return {
        "client_name": "Test Company",
        "website": "https://example.com",
        "industry": "Technology",
        "geography": "United States",
        "primary_offer": "SaaS Platform",
        "objective": "Lead Generation",
        "target_audience": "B2B Companies",
        "pain_points": "Manual processes",
        "desired_outcomes": "Increased efficiency",
        "timezone": "America/New_York",
        "pricing": "$99/month",
        "differentiators": "AI-powered automation",
        "kpi_targets": "100 leads/month",
        "timeline_start": "2025-01-01",
        "duration_weeks": 12,
        "budget_range": "$10k-$50k",
        "tone_voice": "Professional",
        "languages": ["English"],
        "context_data": {},
        "delivery_requirements": {
            "pdf": True,
            "pptx": False,
            "zip": False,
            "frequency": "One-time"
        }
    }

