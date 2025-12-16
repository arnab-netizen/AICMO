"""Conftest for orchestration tests."""

import sys
from pathlib import Path

# Add workspace root to path
workspace_root = Path(__file__).parent.parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))
