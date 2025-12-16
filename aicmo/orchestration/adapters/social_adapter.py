"""
Social Media POST_SOCIAL Action Adapter.

Handles POST_SOCIAL actions:
- PROOF mode: Write artifact only, record to DB
- REAL mode: Raise REAL_RUN_UNCONFIGURED error

NO interpretation allowed. Exact action execution only.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from sqlalchemy.orm import Session

from aicmo.orchestration.queue import ActionQueue


class RealRunUnconfigured(Exception):
    """Raised when attempting REAL mode action without proper configuration."""
    pass


def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hex digest of data."""
    return hashlib.sha256(data).hexdigest()


def handle_post_social(
    session: Session,
    action_id: int,
    payload: Dict[str, Any],
    proof_mode: bool = False,
) -> None:
    """
    Execute POST_SOCIAL action.
    
    PROOF mode:
    - Payload must have: social_platform, content, audience
    - Write artifact to artifacts/proof_social/<ISO_UTC>_<idempotency_key>.txt
    - Compute SHA256 and store in execution log
    - Mark action SUCCESS
    
    REAL mode:
    - Raise RealRunUnconfigured with execution log FAIL
    
    Args:
        session: SQLAlchemy session
        action_id: AOL action ID
        payload: Action payload dict
        proof_mode: True = PROOF, False = REAL
    """
    
    try:
        # Validate payload (must have these keys)
        required_keys = {"social_platform", "content", "audience"}
        if not all(k in payload for k in required_keys):
            error_msg = f"Missing required keys: {required_keys}. Got: {set(payload.keys())}"
            ActionQueue.log_execution(
                session, action_id, "ERROR", error_msg
            )
            raise ValueError(error_msg)
        
        if not proof_mode:
            # REAL mode: raise error
            error_msg = "REAL_RUN_UNCONFIGURED: Real social posting not configured in this environment"
            ActionQueue.log_execution(
                session, action_id, "ERROR", error_msg
            )
            ActionQueue.mark_failed(session, action_id, error_msg)
            raise RealRunUnconfigured(error_msg)
        
        # PROOF mode: write artifact
        now_utc_iso = datetime.utcnow().isoformat().replace(":", "-").replace("+", "_")
        
        # Create artifacts directory if needed
        artifacts_dir = Path("/tmp/artifacts/proof_social")  # Safe location
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Build artifact filename
        idempotency_key = payload.get("idempotency_key", f"post_{action_id}")
        artifact_filename = f"{now_utc_iso}_{idempotency_key}.txt"
        artifact_path = artifacts_dir / artifact_filename
        
        # Build artifact content
        artifact_content = f"""POST_SOCIAL Action (PROOF Mode)
Generated: {datetime.utcnow().isoformat()}
Action ID: {action_id}

Payload:
{json.dumps(payload, indent=2)}

Social Platform: {payload.get('social_platform', 'N/A')}
Content: {payload.get('content', 'N/A')}
Audience: {payload.get('audience', 'N/A')}

This is a PROOF mode artifact - no real post sent.
"""
        
        # Write artifact
        artifact_bytes = artifact_content.encode('utf-8')
        artifact_path.write_bytes(artifact_bytes)
        
        # Compute SHA256
        artifact_sha256 = compute_sha256(artifact_bytes)
        
        # Log execution with artifact metadata
        ActionQueue.log_execution(
            session, action_id, "INFO",
            f"PROOF mode artifact written: {artifact_path}",
            artifact_ref=str(artifact_path),
            artifact_sha256=artifact_sha256,
        )
        
        # Mark SUCCESS
        ActionQueue.mark_success(session, action_id)
        
    except RealRunUnconfigured:
        # Already logged and marked failed
        raise
    except Exception as e:
        error_msg = f"POST_SOCIAL action failed: {str(e)}"
        ActionQueue.log_execution(session, action_id, "ERROR", error_msg)
        ActionQueue.mark_failed(session, action_id, error_msg)
        raise
