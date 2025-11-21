FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Copy repository early so editable installs (like -e ./capsule-core) resolve
COPY . /app/backend

# Safety: remove any stray top-level 'types.py' that would shadow the stdlib module
RUN rm -f /app/backend/types.py || true

WORKDIR /app/backend

# system deps (psycopg build, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Install Python requirements from the repository
RUN pip install --upgrade pip && pip install -r requirements.txt

# temporalio is required by some routers at import-time; ensure it's installed
RUN pip install temporalio==1.18.1 || true
 
# Ensure hatchling is available for editable installs that use hatch build backend
RUN pip install hatchling>=1.25.0 || true

# Explicitly install the in-tree capsule-core package in editable mode
RUN pip install -e ./capsule-core || true

EXPOSE 8000

# Run uvicorn with PYTHONPATH pointing to the backend package folder only.
CMD ["bash", "-lc", "uvicorn backend.app:app --host 0.0.0.0 --port 8000"]
