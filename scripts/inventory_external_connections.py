#!/usr/bin/env python3
"""
Scan the repo for external-connection signals and emit:
- Markdown table to stdout
- ./docs/external-connections.md (same content)
- ./.env.example (best-effort from discovered env names)

Signals:
- Client SDK imports (db/s3/queue/llm/email/payments/analytics)
- Env var usages (os.environ["X"], os.getenv("X"), process.env.X)
- URLs/hosts/ports
- Workflow secrets in .github/workflows
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

INCLUDE_GLOBS = ["backend", "frontend", ".github", "docker", "infra", "config", "alembic"]
EXTS = (
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".json",
    ".yml",
    ".yaml",
    ".env",
    ".toml",
    ".ini",
    ".sh",
    ".md",
)

CLIENT_PATTERNS = {
    "Database": r"\b(asyncpg|psycopg|sqlalchemy|pgvector)\b",
    "Object Storage": r"\b(boto3|minio|aiobotocore)\b",
    "Cache/Queue": r"\b(redis|rq|celery|pika|kafka|confluent)\b",
    "Orchestrator": r"\b(temporalio)\b",
    "LLM": r"\b(openai|anthropic|vertexai|groq|together|cohere)\b",
    "HTTP APIs": r"\b(httpx|requests)\b",
    "Email/SMS": r"\b(sendgrid|smtplib|smtp|twilio)\b",
    "Payments": r"\b(stripe|razorpay|paypal)\b",
    "Analytics/Telemetry": r"\b(segment|posthog|mixpanel|sentry|opentelemetry)\b",
}

# Additional high-signal clients
CLIENT_PATTERNS.update(
    {
        "Migrations": r"\b(alembic)\b",
        "Web Framework": r"\b(fastapi|starlette)\b",
        "Config": r"\b(BaseSettings|pydantic_settings|python-dotenv|load_dotenv)\b",
    }
)

ENV_PATTERNS = [
    r"os\.environ\[\s*[\'\"]([A-Z0-9_]+)[\'\"]\s*\]",
    r"os\.getenv\(\s*[\'\"]([A-Z0-9_]+)[\'\"]\s*[,)]",
    r"process\.env\.([A-Z0-9_]+)",
]

URL_PATTERN = r"(?P<url>(?:https?://|postgres(?:ql)?://|redis://|amqp://|s3://)[^\s\'\")]+)"


# crude category guess from env var name
def guess_category(name: str) -> str:
    n = name.upper()
    if any(k in n for k in ["POSTGRES", "PG", "DATABASE_URL", "SQLALCHEMY"]):
        return "Database"
    if any(k in n for k in ["S3", "MINIO", "AWS_", "BUCKET", "OBJECT_STORE"]):
        return "Object Storage"
    if any(k in n for k in ["REDIS", "CELERY", "KAFKA", "RABBIT", "AMQP"]):
        return "Cache/Queue"
    if "TEMPORAL" in n:
        return "Orchestrator"
    if any(k in n for k in ["OPENAI", "ANTHROPIC", "GROQ", "COHERE", "VERTEX", "LLM"]):
        return "LLM"
    if any(k in n for k in ["SMTP", "SENDGRID", "EMAIL", "TWILIO"]):
        return "Email/SMS"
    if any(k in n for k in ["STRIPE", "RAZORPAY", "PAYPAL"]):
        return "Payments"
    if any(k in n for k in ["SEGMENT", "POSTHOG", "MIXPANEL", "SENTRY", "OTEL", "OPENTELEMETRY"]):
        return "Analytics/Telemetry"
    if any(k in n for k in ["JWT", "OAUTH", "ISSUER", "AUDIENCE"]):
        return "Auth/Identity"
    return "HTTP APIs"


def iter_files():
    for g in INCLUDE_GLOBS:
        p = ROOT / g
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if f.is_file() and f.suffix.lower() in EXTS and ".venv" not in str(f):
                yield f


def main():
    findings = defaultdict(
        lambda: defaultdict(list)
    )  # category -> key ("env","client","url") -> list[(file,line,text)]
    env_names = set()

    client_res = {cat: re.compile(p, re.I) for cat, p in CLIENT_PATTERNS.items()}
    env_res = [re.compile(p) for p in ENV_PATTERNS]
    url_re = re.compile(URL_PATTERN)

    for f in iter_files():
        try:
            text = f.read_text(errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            # clients
            for cat, cre in client_res.items():
                if cre.search(line):
                    findings[cat]["client"].append((f, i, line.strip()))
            # envs
            for er in env_res:
                for m in er.finditer(line):
                    name = m.group(1) if m.groups() else None
                    if not name:
                        # process.env.X regex puts name in group 1 already
                        name = m.group(1)
                    if name and name.isupper():
                        env_names.add(name)
                        cat = guess_category(name)
                        findings[cat]["env"].append((f, i, name))
            # urls
            for m in url_re.finditer(line):
                url = m.group("url")
                cat = (
                    "Database"
                    if url.startswith("postgres")
                    else (
                        "Cache/Queue"
                        if url.startswith(("redis://", "amqp://"))
                        else "Object Storage" if url.startswith("s3://") else "HTTP APIs"
                    )
                )
                findings[cat]["url"].append((f, i, url))

    # Compose rows
    rows = []
    for cat, buckets in findings.items():
        # derive service names crudely from envs
        required_envs = sorted({e[2] for e in buckets.get("env", [])})
        code_refs = []
        for key in ("client", "env", "url"):
            for f, i, snip in buckets.get(key, []):
                code_refs.append(f"{f.relative_to(ROOT)}:{i}")
        code_refs = sorted(set(code_refs))[:30]  # cap
        service_guess = {
            "Database": "Postgres/SQL DB",
            "Object Storage": "S3/MinIO",
            "Cache/Queue": "Redis/Rabbit/Kafka",
            "Orchestrator": "Temporal",
            "LLM": "LLM provider(s)",
            "Email/SMS": "SMTP/SendGrid/Twilio",
            "Payments": "Stripe/Razorpay/PayPal",
            "Analytics/Telemetry": "PostHog/Segment/Sentry/OTel",
            "HTTP APIs": "External HTTP APIs",
        }.get(cat, cat)

        rows.append(
            {
                "Category": cat,
                "Service": service_guess,
                "Purpose": "External connection discovered via code scan",
                "SDK/Client": (
                    ", ".join(
                        sorted(
                            set(
                                re.findall(
                                    CLIENT_PATTERNS.get(cat, ""),
                                    "\n".join([x[2] for x in buckets.get("client", [])]),
                                    flags=re.I,
                                )
                            )
                        )
                    )
                    if buckets.get("client")
                    else ""
                ),
                "Required ENV": ", ".join(required_envs) if required_envs else "",
                "Optional ENV": "",
                "Secrets": ", ".join(
                    [
                        e
                        for e in required_envs
                        if any(k in e for k in ["SECRET", "TOKEN", "KEY", "PASSWORD"])
                    ]
                ),
                "Least-Privilege Notes": "",
                "Local Mock": "See checklist",
                "Code Refs": ", ".join(code_refs),
            }
        )

    # Markdown table
    headers = [
        "Category",
        "Service",
        "Purpose",
        "SDK/Client",
        "Required ENV",
        "Optional ENV",
        "Secrets",
        "Least-Privilege Notes",
        "Local Mock",
        "Code Refs",
    ]
    md = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in sorted(rows, key=lambda x: x["Category"]):
        md.append("| " + " | ".join(r.get(h, "") or "" for h in headers) + " |")

    # Local bring-up (static helper text)
    bringup = """
## Local Bring-Up (quick)
- **Database (Postgres + asyncpg)**: docker run -d --name pg -e POSTGRES_USER=aicmo -e POSTGRES_PASSWORD=pass -e POSTGRES_DB=aicmo -p 5432:5432 postgres:16
- **S3/MinIO**: docker run -d --name minio -e MINIO_ROOT_USER=minio -e MINIO_ROOT_PASSWORD=minio-secret -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address :9001
  - Create bucket: docker run --rm --network host minio/mc sh -c "mc alias set local http://127.0.0.1:9000 minio minio-secret && mc mb -p local/aicmo-assets || true"
- **Temporal (dev)**: docker run -d --name temporalite -p 7233:7233 temporalio/temporalite:latest start --namespace aicmo-dev --ip 0.0.0.0
- **OpenAI (LLM)**: set OPENAI_API_KEY with your key; for offline dev, guard calls or use a mock.
- **Redis (if detected)**: docker run -d --name redis -p 6379:6379 redis:7
- Export envs: `cp .env.example .env && edit`, then `set -a && source .env && set +a`.
"""

    md.append(bringup)

    # Write docs & print
    out_md = "\n".join(md)
    (DOCS / "external-connections.md").write_text(out_md)
    print(out_md)

    # .env.example from env_names + sensible local values
    defaults = {
        "DATABASE_URL": "postgresql+asyncpg://aicmo:pass@localhost:5432/aicmo",
        "S3_ENDPOINT": "http://localhost:9000",
        "S3_BUCKET": "aicmo-assets",
        "S3_REGION": "ap-south-1",
        "S3_ACCESS_KEY_ID": "minio",
        "S3_SECRET_ACCESS_KEY": "minio-secret",
        "JWT_SECRET": "change-me",
        "JWT_AUDIENCE": "aicmo",
        "JWT_ISSUER": "http://aicmo.local",
        "OPENAI_API_KEY": "sk-xxx",
        "TEMPORAL_ADDRESS": "localhost:7233",
        "TEMPORAL_NAMESPACE": "aicmo-dev",
    }

    def guess_value(name: str) -> str:
        for k, v in defaults.items():
            if name.upper() == k:
                return v
        # safe generic placeholders
        if any(t in name for t in ["KEY", "TOKEN", "SECRET", "PASSWORD"]):
            return f"{name.lower()}-here"
        if name.endswith("_URL"):
            return "http://localhost"
        if name.endswith("_HOST"):
            return "localhost"
        if name.endswith("_PORT"):
            return "0000"
        if name.endswith("_USER"):
            return "user"
        if name.endswith("_PASS") or name.endswith("_PASSWORD"):
            return "pass"
        return ""

    env_lines = []
    for n in sorted(env_names):
        env_lines.append(f"{n}={guess_value(n)}")
    # Ensure must-have envs are present
    must_haves = [
        "DATABASE_URL",
        "S3_ENDPOINT",
        "S3_BUCKET",
        "S3_REGION",
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "JWT_SECRET",
        "JWT_AUDIENCE",
        "JWT_ISSUER",
        "OPENAI_API_KEY",
        "TEMPORAL_ADDRESS",
        "TEMPORAL_NAMESPACE",
    ]
    for m in must_haves:
        if m not in env_names:
            env_lines.append(f"{m}={guess_value(m)}")
    (ROOT / ".env.example").write_text("\n".join(env_lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
