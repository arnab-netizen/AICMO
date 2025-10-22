import sys
import re
import pathlib
import ast
from typing import List


SQL_TOKENS = [
    r"\bdrop\s+table\b",
    r"\bdrop\s+column\b",
    r"\balter\s+table\b.*\bdrop\b",
    r"\btruncate\b",
    r"\brename\s+column\b",
]

SQL_PAT = re.compile("|".join(SQL_TOKENS), re.IGNORECASE | re.DOTALL)


def _read_whitelist(path: pathlib.Path) -> List[str]:
    fn = path / "autogen_whitelist.txt"
    if not fn.exists():
        return []
    out = []
    for ln in fn.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.split("#", 1)[0].strip()
        if not ln:
            continue
        out.append(ln)
    return out


def _sql_has_destructive(sql: str) -> bool:
    # remove SQL comments -- and /* */
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    return bool(SQL_PAT.search(sql))


def _py_has_destructive(code: str) -> bool:
    """Use AST to detect op.drop_table / op.drop_column / op.drop_index and
    op.execute(...) with destructive SQL strings. This ignores commented-out code.
    """
    try:
        tree = ast.parse(code)
    except Exception:
        # if parsing fails, fall back to a regex scan
        return bool(SQL_PAT.search(code))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # look for op.drop_table, op.drop_column, op.drop_index
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id == "op" and func.attr in {
                    "drop_table",
                    "drop_column",
                    "drop_index",
                }:
                    return True
                if func.value.id == "op" and func.attr == "execute":
                    # check first arg if it's a string literal
                    if node.args:
                        a0 = node.args[0]
                        if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                            if _sql_has_destructive(a0.value):
                                return True
            # also detect calls like op.execute(text("DROP TABLE ...")) where arg is Call(Name 'text')
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "op"
                and func.attr == "execute"
            ):
                if node.args:
                    a0 = node.args[0]
                    # handle a call like text("...") or sa.text("...")
                    if isinstance(a0, ast.Call) and a0.args:
                        first = a0.args[0]
                        if isinstance(first, ast.Constant) and isinstance(first.value, str):
                            if _sql_has_destructive(first.value):
                                return True
    return False


def scan_dir(d: pathlib.Path):
    hits = []
    whitelist = _read_whitelist(d.parent if d.is_file() else d)
    for p in d.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.name)
        if rel in whitelist or str(p) in whitelist:
            continue
        suf = p.suffix.lower()
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if suf == ".sql":
            if _sql_has_destructive(t):
                hits.append(p)
        elif suf == ".py":
            if _py_has_destructive(t):
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
