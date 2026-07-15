# TITAN Core Backend

This directory contains the TITAN OS backend foundation and the Phase 2.3.2 Fixture Ingestion Pipeline. It provides the API host, configuration, PostgreSQL and Redis clients, migrations, structured logging, authentication extension points, observability, canonical Sports Domain, and auditable provider-neutral fixture ingestion.

It intentionally contains no odds, statistics, research, machine learning, probability, consensus, risk, explainability, recommendation, or backtesting implementation.

## Prerequisites

- Python 3.12 or later
- Docker Desktop and Docker Compose (recommended for PostgreSQL and Redis)

## Run with Docker Compose

From the repository root:

```powershell
docker compose up --build
```

The API is available at `http://localhost:8000`.

- Health: `GET http://localhost:8000/health`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Swagger UI: `http://localhost:8000/docs` in development
- Metrics: `http://localhost:8000/metrics`

Copy `backend/.env.example` to a root `.env` file before overriding Docker Compose defaults. Do not use the development database password or secret key outside local development.

## Run locally

Run these commands from `backend/`:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For a local process, start PostgreSQL and Redis through Docker Compose first, then keep the `TITAN_DATABASE_URL` and `TITAN_REDIS_URL` values from `.env.example`.

## Fixture ingestion

The protected internal endpoint accepts a batch of raw provider payloads:

```text
POST /api/v1/ingestion/fixtures/fixture_feed_v1
Authorization: Bearer <configured-token>
```

Its response is a per-payload summary of inserted, updated, unchanged, and validation-failed outcomes. The full raw JSON is kept only in PostgreSQL for auditability; it is never echoed by the API.

`fixture_feed_v1` is a reference adapter and demonstrates the expected provider-specific contract. Follow [the ingestion module guide](app/modules/ingestion/README.md) to add a new provider adapter without changing canonical Sports Domain models or ingestion business logic.

## Database migrations

Alembic includes the canonical Sports Domain migration and the Fixture Ingestion Pipeline migration. Future bounded modules must add their own reviewed migrations rather than modifying historical revisions.

```powershell
alembic upgrade head
alembic revision --autogenerate -m "describe the change"
```

Run migration commands from `backend/`. Review every generated migration before applying it.

## Tests and checks

```powershell
pytest
ruff check .
```

The database connectivity test runs when `TITAN_TEST_DATABASE_URL` is set. To run it locally against the Compose database, start `db` first and set `TITAN_TEST_DATABASE_URL` to `postgresql+asyncpg://titan:titan@localhost:5432/titan` before running `pytest`. Without that explicit test URL, the test is intentionally skipped rather than attempting to connect to an unknown database.

## Production notes

- Set a unique `TITAN_SECRET_KEY` through a secrets manager.
- Set `TITAN_APP_ENV=production`, disable interactive documentation unless protected, and configure non-local CORS origins.
- Keep `/metrics` private at the network or ingress layer.
- Use managed PostgreSQL, Redis, backups, TLS, and a secrets manager before production deployment.
