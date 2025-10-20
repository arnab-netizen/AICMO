#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:=postgresql+asyncpg://aicmo:pass@localhost:5432/aicmo}"
: "${S3_ENDPOINT:=http://localhost:9000}"
: "${S3_BUCKET:=aicmo-assets}"
: "${TEMPORAL_ADDRESS:=localhost:7233}"
: "${TEMPORAL_NAMESPACE:=aicmo-dev}"

echo "== DB  $DATABASE_URL"
python - <<'PY'
import os, asyncio
try:
    import asyncpg
except Exception as e:
    print('asyncpg not installed:', e)
    raise
async def main():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg','postgresql')
    conn = await asyncpg.connect(url)
    v = await conn.fetchval('select 1')
    print('DB OK:', v)
    await conn.close()
asyncio.run(main())
PY

echo "== S3 -> $S3_ENDPOINT / $S3_BUCKET"
if command -v aws >/dev/null 2>&1; then
  aws --endpoint-url "$S3_ENDPOINT" s3 ls "s3://$S3_BUCKET" >/dev/null && echo "S3 OK" || (echo "S3 LIST FAILED"; exit 1)
else
  # fallback: MinIO health + bucket HEAD
  curl -fsS "$S3_ENDPOINT/minio/health/live" >/dev/null && echo "MinIO live" || (echo "MinIO health check failed"; exit 1)
  # best-effort: attempt to list via mc if containerized alias exists
  echo "(Tip) Install AWS CLI for a stronger S3 smoke: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
fi

echo "== Temporal -> $TEMPORAL_ADDRESS / $TEMPORAL_NAMESPACE"
docker run --rm --network host temporalio/admin-tools:latest \
  tctl --address "$TEMPORAL_ADDRESS" namespace describe --namespace "$TEMPORAL_NAMESPACE" >/dev/null \
  && echo "Temporal OK" || (echo "Temporal FAILED"; exit 1)
