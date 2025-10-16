FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# system deps (psycopg build, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# requirements (reuse your existing requirements.txt at repo root or backend/)
# If your requirements file is at repo root, change the COPY path accordingly.
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# app code
COPY . /app

EXPOSE 8000

# Default command can be overridden by docker-compose for worker/api
CMD ["bash", "-lc", "uvicorn backend.app:app --host 0.0.0.0 --port 8000"]
