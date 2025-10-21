import sys
import re
import pathlib

TOKENS = [
    r"\bdrop\s+table\b",
    r"\bdrop\s+column\b",
    r"\balter\s+table\b.*\bdrop\b",
    r"\btruncate\b",
    r"\brename\s+column\b",
    r"\bop\.drop_table\b",
    r"\bop\.drop_column\b",
    r"\bop\.execute\([^)]*\bdrop\b",
]

PAT = re.compile("|".join(TOKENS), re.IGNORECASE | re.DOTALL)


def scan_dir(d: pathlib.Path):
    hits = []
    for p in d.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".py", ".sql"}:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if PAT.search(t):
                hits.append(p)
    return hits


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/scan_autogen_for_drops.py <dir1> [dir2 ...]")
        sys.exit(2)
    bad = []
    for arg in sys.argv[1:]:
        d = pathlib.Path(arg)
        if d.exists():
            bad.extend(scan_dir(d))
    if bad:
        print("!! Destructive-looking tokens found in:")
        for p in bad:
            print(" -", p)
        sys.exit(1)
    print("No destructive tokens found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
