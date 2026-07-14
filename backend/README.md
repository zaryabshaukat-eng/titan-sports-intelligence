# TITAN Core Backend Foundation

This directory contains only the Phase 2.2 backend foundation for TITAN OS. It provides the API host, configuration, PostgreSQL and Redis clients, migrations, structured logging, authentication extension points, observability, and initial tests.

It intentionally contains no fixture ingestion, odds, statistics, research, machine learning, probability, consensus, risk, recommendation, or backtesting implementation.

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

## Database migrations

Alembic is configured, but this foundation deliberately includes no domain schema migrations. Future modules own their migrations.

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
