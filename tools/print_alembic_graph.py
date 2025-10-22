import pathlib
import re
from collections import defaultdict

VERS = pathlib.Path("backend/alembic/versions")
RX_REV = re.compile(r"^\s*revision\s*=\s*[\'\"]([^\'\"]+)[\'\"]", re.M)
RX_DOWN = re.compile(r"^\s*down_revision\s*=\s*[\'\"]([^\'\"]*)[\'\"]", re.M)


def parse_headers(p: pathlib.Path):
    text = p.read_text(encoding="utf-8", errors="ignore")
    rev = RX_REV.search(text)
    down = RX_DOWN.search(text)
    return (rev.group(1) if rev else None, down.group(1) if down else None)


def main():
    nodes = {}
    parents = defaultdict(list)
    children = defaultdict(list)

    for f in sorted(VERS.glob("*.py")):
        rev, down = parse_headers(f)
        if rev:
            nodes[rev] = f.name
            if down:
                parents[rev].append(down)
                children[down].append(rev)

    print("== Alembic revision graph (rev -> down_revision) ==")
    for rev, fname in nodes.items():
        print(f"{rev:35s}  <- {', '.join(parents.get(rev, ['None']))}  [{fname}]")

    missing = [p for revs in parents.values() for p in revs if p and p not in nodes]
    if missing:
        print("\n!! Missing referenced down_revision(s):")
        for m in sorted(set(missing)):
            print(" -", m)

    roots = [r for r in nodes if not parents.get(r) or parents.get(r) == ["None"]]
    heads = [r for r in nodes if r not in children]
    print(f"\nRoots: {roots}")
    print(f"Heads: {heads}")


if __name__ == "__main__":
    main()
