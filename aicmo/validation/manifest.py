"""
Artifact Manifest Generator

Creates and manages artifact manifests for client deliveries.
Ensures all outputs are tracked and validated before delivery.
"""

import os
import hashlib
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class ArtifactInfo:
    """Information about a single artifact."""
    artifact_id: str
    filename: str
    path: str
    size_bytes: int
    checksum_sha256: str
    schema_version: str
    format: str
    section_map_path: Optional[str] = None
    validation_report_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ArtifactManifest:
    """Complete manifest for a client delivery."""
    manifest_version: str
    run_id: str
    client_id: str
    project_id: str
    timestamp: str
    artifacts: List[ArtifactInfo]
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'artifacts': [a.to_dict() for a in self.artifacts]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, filepath: str) -> None:
        """Save manifest to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @staticmethod
    def load(filepath: str) -> 'ArtifactManifest':
        """Load manifest from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        artifacts = [ArtifactInfo(**a) for a in data['artifacts']]
        return ArtifactManifest(
            manifest_version=data['manifest_version'],
            run_id=data['run_id'],
            client_id=data['client_id'],
            project_id=data['project_id'],
            timestamp=data['timestamp'],
            artifacts=artifacts,
            metadata=data['metadata']
        )


class ManifestGenerator:
    """Generates artifact manifests for client deliveries."""
    
    MANIFEST_VERSION = "1.0.0"
    
    @staticmethod
    def calculate_checksum(filepath: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Get file size in bytes."""
        return os.path.getsize(filepath)
    
    def create_artifact_info(
        self,
        artifact_id: str,
        filepath: str,
        schema_version: str,
        section_map_path: Optional[str] = None
    ) -> ArtifactInfo:
        """Create artifact info from a file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Artifact file not found: {filepath}")
        
        filename = os.path.basename(filepath)
        file_ext = Path(filepath).suffix.lstrip('.')
        size_bytes = self.get_file_size(filepath)
        checksum = self.calculate_checksum(filepath)
        
        return ArtifactInfo(
            artifact_id=artifact_id,
            filename=filename,
            path=filepath,
            size_bytes=size_bytes,
            checksum_sha256=checksum,
            schema_version=schema_version,
            format=file_ext,
            section_map_path=section_map_path
        )
    
    def create_manifest(
        self,
        run_id: str,
        client_id: str,
        project_id: str,
        artifacts: List[ArtifactInfo],
        metadata: Optional[Dict] = None
    ) -> ArtifactManifest:
        """Create complete artifact manifest."""
        return ArtifactManifest(
            manifest_version=self.MANIFEST_VERSION,
            run_id=run_id,
            client_id=client_id,
            project_id=project_id,
            timestamp=datetime.utcnow().isoformat(),
            artifacts=artifacts,
            metadata=metadata or {}
        )
    
    def create_from_directory(
        self,
        run_id: str,
        client_id: str,
        project_id: str,
        artifact_dir: str,
        artifact_configs: List[Dict],
        metadata: Optional[Dict] = None
    ) -> ArtifactManifest:
        """
        Create manifest from all artifacts in a directory.
        
        Args:
            run_id: Unique run identifier
            client_id: Client identifier
            project_id: Project identifier
            artifact_dir: Directory containing artifacts
            artifact_configs: List of dicts with artifact_id, filename, schema_version
            metadata: Optional metadata
            
        Returns:
            Complete ArtifactManifest
        """
        artifacts = []
        
        for config in artifact_configs:
            filepath = os.path.join(artifact_dir, config['filename'])
            section_map_path = filepath.replace(
                Path(filepath).suffix,
                '.section_map.json'
            )
            
            # Check if section map exists
            if not os.path.exists(section_map_path):
                section_map_path = None
            
            artifact_info = self.create_artifact_info(
                artifact_id=config['artifact_id'],
                filepath=filepath,
                schema_version=config['schema_version'],
                section_map_path=section_map_path
            )
            artifacts.append(artifact_info)
        
        return self.create_manifest(
            run_id=run_id,
            client_id=client_id,
            project_id=project_id,
            artifacts=artifacts,
            metadata=metadata
        )
    
    def verify_manifest(self, manifest: ArtifactManifest) -> Dict:
        """
        Verify manifest integrity by checking all artifacts exist and checksums match.
        
        Returns:
            Dict with verification results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        for artifact in manifest.artifacts:
            # Check file exists
            if not os.path.exists(artifact.path):
                results['valid'] = False
                results['errors'].append(
                    f"Artifact not found: {artifact.path}"
                )
                continue
            
            # Verify checksum
            actual_checksum = self.calculate_checksum(artifact.path)
            if actual_checksum != artifact.checksum_sha256:
                results['valid'] = False
                results['errors'].append(
                    f"Checksum mismatch for {artifact.filename}: "
                    f"expected {artifact.checksum_sha256}, got {actual_checksum}"
                )
            
            # Check section map if referenced
            if artifact.section_map_path:
                if not os.path.exists(artifact.section_map_path):
                    results['warnings'].append(
                        f"Section map not found: {artifact.section_map_path}"
                    )
        
        return results


# Example usage
def example_manifest_creation():
    """Example of creating a manifest for a client delivery."""
    generator = ManifestGenerator()
    
    # After generating all artifacts
    artifact_configs = [
        {
            'artifact_id': 'marketing_strategy_report_pdf',
            'filename': 'marketing_strategy_report.pdf',
            'schema_version': '1.0.0'
        },
        {
            'artifact_id': 'marketing_strategy_pptx',
            'filename': 'marketing_strategy_deck.pptx',
            'schema_version': '1.0.0'
        }
    ]
    
    manifest = generator.create_from_directory(
        run_id="run_e2e_20251215_001",
        client_id="client_123",
        project_id="project_456",
        artifact_dir="artifacts/e2e/run_e2e_20251215_001",
        artifact_configs=artifact_configs,
        metadata={
            'environment': 'e2e',
            'proof_run': True,
            'test_seed': 'e2e-deterministic-seed-2025'
        }
    )
    
    # Save manifest
    manifest.save("artifacts/e2e/run_e2e_20251215_001/manifest.json")
    
    # Verify before delivery
    verification = generator.verify_manifest(manifest)
    if not verification['valid']:
        raise ValueError(f"Manifest verification failed: {verification['errors']}")
    
    return manifest
