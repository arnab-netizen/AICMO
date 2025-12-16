"""
Runtime artifact paths for E2E Client Output Gate.

Provides standardized paths for artifacts, manifests, validation reports.
Enforces E2E mode requirements and fail-fast on misconfiguration.
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class RuntimePathError(Exception):
    """Raised when runtime path configuration is invalid."""
    pass


class RuntimePaths:
    """Manages artifact paths for E2E gate integration."""
    
    def __init__(
        self,
        run_id: Optional[str] = None,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """
        Initialize runtime paths.
        
        Args:
            run_id: Unique run identifier (defaults to timestamp)
            client_id: Client identifier
            project_id: Project identifier
        """
        self.e2e_mode = os.getenv('AICMO_E2E_MODE') == '1'
        self.artifact_dir_base = os.getenv('AICMO_E2E_ARTIFACT_DIR')
        
        # Fail-fast if E2E mode enabled but artifact dir missing
        if self.e2e_mode and not self.artifact_dir_base:
            raise RuntimePathError(
                "E2E mode enabled (AICMO_E2E_MODE=1) but AICMO_E2E_ARTIFACT_DIR not set"
            )
        
        # Generate run_id if not provided
        self.run_id = run_id or self._generate_run_id()
        self.client_id = client_id or "default_client"
        self.project_id = project_id or "default_project"
        
        # Create base paths
        if self.e2e_mode:
            self._ensure_directories()
    
    def _generate_run_id(self) -> str:
        """Generate deterministic run ID using seed if available."""
        seed = os.getenv('AICMO_TEST_SEED')
        if seed:
            # Use seed + timestamp for uniqueness within test session
            return f"run_{seed}_{int(datetime.utcnow().timestamp())}"
        return f"run_{int(datetime.utcnow().timestamp())}"
    
    @property
    def run_dir(self) -> Path:
        """Base directory for this run."""
        if not self.e2e_mode:
            return Path("/tmp/aicmo_artifacts") / self.run_id
        return Path(self.artifact_dir_base) / self.run_id
    
    @property
    def manifest_dir(self) -> Path:
        """Directory for manifest files."""
        return self.run_dir / "manifest"
    
    @property
    def validation_dir(self) -> Path:
        """Directory for validation reports."""
        return self.run_dir / "validation"
    
    @property
    def downloads_dir(self) -> Path:
        """Directory for client-facing download files."""
        return self.run_dir / "downloads"
    
    @property
    def logs_dir(self) -> Path:
        """Directory for logs."""
        return self.run_dir / "logs"
    
    @property
    def manifest_path(self) -> Path:
        """Path to manifest JSON."""
        return self.manifest_dir / "client_output_manifest.json"
    
    @property
    def validation_path(self) -> Path:
        """Path to validation report JSON."""
        return self.validation_dir / "client_output_validation.json"
    
    @property
    def section_map_path(self) -> Path:
        """Path to section map JSON."""
        return self.validation_dir / "section_map.json"
    
    def get_download_path(self, filename: str) -> Path:
        """
        Get path for a download file.
        
        Args:
            filename: Name of the file
            
        Returns:
            Full path in downloads directory
        """
        return self.downloads_dir / filename
    
    def _ensure_directories(self) -> None:
        """Create all required directories."""
        for dir_path in [
            self.run_dir,
            self.manifest_dir,
            self.validation_dir,
            self.downloads_dir,
            self.logs_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        """Export paths as dictionary for logging/debugging."""
        return {
            "run_id": self.run_id,
            "client_id": self.client_id,
            "project_id": self.project_id,
            "e2e_mode": self.e2e_mode,
            "run_dir": str(self.run_dir),
            "manifest_path": str(self.manifest_path),
            "validation_path": str(self.validation_path),
            "section_map_path": str(self.section_map_path),
            "downloads_dir": str(self.downloads_dir),
        }


# Global singleton for current run
_current_paths: Optional[RuntimePaths] = None


def get_runtime_paths(
    run_id: Optional[str] = None,
    client_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> RuntimePaths:
    """
    Get or create runtime paths for current run.
    
    Args:
        run_id: Optional run ID (creates new if not provided)
        client_id: Optional client ID
        project_id: Optional project ID
        
    Returns:
        RuntimePaths instance
    """
    global _current_paths
    
    # If requesting specific run_id, always create new
    if run_id:
        return RuntimePaths(run_id, client_id, project_id)
    
    # Otherwise use singleton
    if _current_paths is None:
        _current_paths = RuntimePaths(None, client_id, project_id)
    
    return _current_paths


def reset_runtime_paths() -> None:
    """Reset runtime paths (for testing/diagnostics)."""
    global _current_paths
    _current_paths = None
