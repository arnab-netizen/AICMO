"""Fatal exception hook for E2E diagnostics.

Ensures ALL unhandled exceptions are visible in:
- Streamlit UI (red box with stack trace)
- /tmp/aicmo_streamlit_e2e.log (stderr)
- fatal_exception.json file in AICMO_E2E_ARTIFACT_DIR

Call install_fatal_exception_hook() at the very top of app.py
BEFORE any other imports that might fail.
"""
import sys
import threading
import traceback
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def install_fatal_exception_hook(artifact_dir: Optional[str] = None) -> None:
    """
    Install global exception hook that surfaces all exceptions.
    
    Args:
        artifact_dir: Directory to write fatal_exception.json. 
                      Falls back to /tmp/aicmo_e2e_artifacts if not specified.
    """
    if artifact_dir is None:
        artifact_dir = os.getenv('AICMO_E2E_ARTIFACT_DIR', '/tmp/aicmo_e2e_artifacts')
    
    Path(artifact_dir).mkdir(parents=True, exist_ok=True)
    
    original_excepthook = sys.excepthook
    original_threading_excepthook = threading.excepthook
    
    def fatal_hook(exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        """Global exception hook that logs fatal errors."""
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Write to stderr with unique marker
        marker = "AICMO_FATAL_EXCEPTION"
        sys.stderr.write(f"\n{'='*80}\n")
        sys.stderr.write(f"{marker}\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(tb_str)
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.flush()
        
        # Write to JSON file
        try:
            fatal_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "marker": marker,
                "exception_type": exc_type.__name__ if exc_type else "Unknown",
                "exception_message": str(exc_value) if exc_value else "Unknown",
                "traceback": tb_str,
                "environment": {
                    "AICMO_E2E_MODE": os.getenv('AICMO_E2E_MODE'),
                    "AICMO_PERSISTENCE_MODE": os.getenv('AICMO_PERSISTENCE_MODE'),
                    "PYTHONPATH": os.getenv('PYTHONPATH'),
                }
            }
            fatal_json = Path(artifact_dir) / "fatal_exception.json"
            fatal_json.write_text(json.dumps(fatal_data, indent=2))
        except Exception as e:
            sys.stderr.write(f"Failed to write fatal_exception.json: {e}\n")
        
        # Call original hook
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    def threading_fatal_hook(args: Any) -> None:
        """Thread exception hook."""
        fatal_hook(args.exc_type, args.exc_value, args.exc_traceback)
    
    sys.excepthook = fatal_hook
    threading.excepthook = threading_fatal_hook
