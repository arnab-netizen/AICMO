# Alembic Usage

- Runtime app uses `postgresql+asyncpg`.
- Alembic swaps to `postgresql+psycopg2` for **online** migrations.
- **Online requires**: `DATABASE_URL` starting with `postgresql`.
- **Offline** (`--sql`) works with no DB.

## Common Commands
- Render SQL offline:
  `ALEMBIC_CONFIG=backend/alembic.ini alembic -c backend/alembic.ini upgrade head --sql`
- Apply online (dev DB):
  `python -m pip install -r backend/requirements.txt && alembic -c backend/alembic.ini upgrade head`

## CI Notes
- `ci-lite` runs two unit tests for URL swap + offline behavior.
- Fails if multiple heads are present (check_single_head.py).
- Conditionally runs online migrations when `DATABASE_URL` contains `postgresql`.
