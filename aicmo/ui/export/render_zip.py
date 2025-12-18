"""
ZIP Renderer for AICMO Delivery Packages

Packages all export files into a single ZIP archive.
"""

import os
import zipfile
from typing import Dict, Any
from datetime import datetime


def render_delivery_zip(
    path: str,
    files_dict: Dict[str, str],
    manifest: Dict[str, Any]
) -> str:
    """
    Generate ZIP archive containing all export files.
    
    Args:
        path: Output ZIP file path
        files_dict: Dict of format -> filepath
        manifest: Delivery manifest dict
    
    Returns:
        Path to generated ZIP
    """
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all generated files
        for format_name, filepath in files_dict.items():
            if os.path.exists(filepath):
                arcname = os.path.basename(filepath)
                zipf.write(filepath, arcname=arcname)
        
        # Add README
        readme_content = _generate_readme(manifest, files_dict)
        zipf.writestr("README.txt", readme_content)
    
    return path


def _generate_readme(manifest: Dict[str, Any], files_dict: Dict[str, str]) -> str:
    """Generate README content"""
    
    campaign_id = manifest["ids"].get("campaign_id", "Unknown")
    client_id = manifest["ids"].get("client_id", "Unknown")
    engagement_id = manifest["ids"].get("engagement_id", "Unknown")
    
    readme = f"""
AICMO Delivery Package
======================

Campaign: {campaign_id}
Client: {client_id}
Engagement: {engagement_id}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Package Contents
----------------
"""
    
    # List files
    for format_name, filepath in sorted(files_dict.items()):
        filename = os.path.basename(filepath)
        readme += f"- {filename}\n"
    
    readme += "\nmanifest.json - Package metadata and checksums\n"
    readme += "README.txt - This file\n"
    
    readme += f"""
Included Artifacts
------------------
"""
    
    for artifact_info in manifest.get("included_artifacts", []):
        artifact_type = artifact_info["type"]
        status = artifact_info["status"]
        version = artifact_info["version"]
        readme += f"- {artifact_type.upper()} (v{version}, {status})\n"
    
    readme += f"""
Pre-Flight Checks
-----------------
Approvals: {'✓' if manifest['checks']['approvals_ok'] else '✗'}
Completeness: {'✓' if manifest['checks']['completeness_ok'] else '✗'}
Branding: {'✓' if manifest['checks']['branding_ok'] else '✗'}
Legal: {'✓' if manifest['checks']['legal_ok'] else '✗'}

Manifest Hash: {manifest.get('manifest_hash', 'N/A')}

---
Prepared by {manifest.get('branding', {}).get('agency_name', 'AICMO')}
"""
    
    return readme
