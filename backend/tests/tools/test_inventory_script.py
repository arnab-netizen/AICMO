import pathlib
import subprocess
import sys
import textwrap


def test_inventory_runs_and_writes_docs(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "backend").mkdir(parents=True)
    (repo / "docs").mkdir(parents=True)
    (repo / "scripts").mkdir(parents=True)

    # Seed a minimal backend file that references envs (so the script finds them)
    (repo / "backend" / "probe.py").write_text(
        textwrap.dedent(
            """
        import os, httpx
        DB = os.getenv("DATABASE_URL")
        KEY = os.environ.get("OPENAI_API_KEY")
        S3 = os.getenv("S3_ENDPOINT")
    """
        )
    )

    # Copy the actual script into the temp repo
    src = pathlib.Path("scripts/inventory_external_connections.py").read_text()
    (repo / "scripts" / "inventory_external_connections.py").write_text(src)

    subprocess.check_call(
        [sys.executable, str(repo / "scripts" / "inventory_external_connections.py")], cwd=repo
    )
    assert (repo / "docs" / "external-connections.md").exists()
    assert (repo / ".env.example").exists()

    md = (repo / "docs" / "external-connections.md").read_text()
    env = (repo / ".env.example").read_text()

    # sanity: the must-have envs should be present
    for key in ["DATABASE_URL", "OPENAI_API_KEY", "S3_ENDPOINT"]:
        assert key in env
        assert key in md or "HTTP APIs" in md
