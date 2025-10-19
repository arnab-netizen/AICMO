$ErrorActionPreference = "Stop"

if (-not $env:DATABASE_URL) { $env:DATABASE_URL = "postgresql+asyncpg://USER:PASS@HOST:5432/DB" }
$py = "python"

Write-Host "==> Using DATABASE_URL=$env:DATABASE_URL"

# 1) venv + deps
& $py -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r backend/requirements.txt

# 2) Migrations (needs psql in PATH)
psql $env:DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
psql $env:DATABASE_URL -f backend/migrations/0001_capsule_shared.sql 2>$null; if ($LASTEXITCODE -ne 0) { Write-Host "warn: 0001 may already be applied" }
psql $env:DATABASE_URL -f backend/migrations/0002_copyhook.sql        2>$null; if ($LASTEXITCODE -ne 0) { Write-Host "warn: 0002 may already be applied" }
psql $env:DATABASE_URL -f backend/migrations/0003_shared_extras.sql
psql $env:DATABASE_URL -f backend/migrations/0004_visualgen_policy.sql

# 3) Boot + health
Start-Process -NoNewWindow -FilePath uvicorn -ArgumentList "backend.app:app","--port","8000","--reload"
Start-Sleep -Seconds 3
Invoke-RestMethod http://localhost:8000/health | Out-Host

# 4) Smoke
$copyhook = '{"project_id":"11111111-1111-1111-1111-111111111111","goal":"landing hero","constraints":{"brand":"Acme","tone":"confident, simple","must_avoid":[]}}'
Invoke-RestMethod http://localhost:8000/api/copyhook/run -Method POST -ContentType 'application/json' -Body $copyhook | ConvertTo-Json -Depth 6 | Out-Host

$visualgen = '{"project_id":"22222222-2222-2222-2222-222222222222","goal":"3 creatives","constraints":{"brand":"Acme","size":"1200x628","count":3}}'
Invoke-RestMethod http://localhost:8000/api/visualgen/run -Method POST -ContentType 'application/json' -Body $visualgen | ConvertTo-Json -Depth 6 | Out-Host
