#!/usr/bin/env python
"""Scan for stub markers, TODOs, and unfinished code patterns."""

import re
import sys
from pathlib import Path

# Adjust if your repo root is different
ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "alembic",  # Skip migrations – they often have pass statements
    "_gh_artifacts",
    ".venv-1",  # Skip specific venv
    "site-packages",  # Skip installed packages
}

STUB_PATTERNS = [
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bSTUB\b",
    r"NotImplementedError",
    r"raise\s+Exception\(['\"]stub['\"]",
    r"lorem ipsum",
    r"sample data only",
    r"temp implementation",
    r"placeholder",
    r"XXX\b",
]

# More specific patterns for "pass" - only flag if it looks like an intentional stub
PASS_PATTERNS = [
    r"pass\s*#.*stub",
    r"pass\s*#.*TODO",
    r"pass\s*#.*FIXME",
]


def iter_files():
    """Yield all Python and JS files, skipping common non-code directories."""
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            continue
        yield path


def main():
    """Scan files for stub patterns and report findings."""
    regexes = [re.compile(p, re.IGNORECASE) for p in STUB_PATTERNS]
    pass_regexes = [re.compile(p, re.IGNORECASE) for p in PASS_PATTERNS]
    hits = 0

    for file in iter_files():
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            # Check main patterns
            for rx in regexes:
                if rx.search(line):
                    print(f"{file}:{i}: {line.strip()}")
                    hits += 1
                    break
            else:
                # Only check pass patterns if main patterns didn't match
                for rx in pass_regexes:
                    if rx.search(line):
                        print(f"{file}:{i}: {line.strip()}")
                        hits += 1
                        break

    if hits:
        print(
            f"\nFound {hits} potential stubs / TODOs (ignoring migrations and routine pass statements)."
        )
        print("Review these for unfinished work before shipping.")
        sys.exit(1)
    else:
        print("No obvious stubs / TODOs found (ignoring migrations).")
        sys.exit(0)


if __name__ == "__main__":
    main()
