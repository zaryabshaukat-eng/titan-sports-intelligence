# TITAN Core Backend

This directory contains the TITAN OS backend foundation, Canonical Sports Domain, Fixture Ingestion, Market Data & Odds, Statistics Ingestion, Feature Store, Research Engine, Probability Engine, Consensus Engine, transactional outbox worker, identity foundation, and observability layer. It provides the API host, configuration, PostgreSQL and Redis clients, migrations, structured logging, RBAC/JWT extension points, auditable ingestion, immutable historical observations, versioned reproducible features, reproducible statistical experiments, calibrated probability evidence, and consensus evidence.

It intentionally contains no machine learning training, risk, explainability, recommendation, or backtesting implementation.

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

## Market Data & Odds Ingestion

The protected internal odds endpoint accepts source-provider batches and writes immutable historical snapshots:

```text
POST /api/v1/market-data/ingestion/odds/odds_feed_v1
Authorization: Bearer <configured-token>
```

It resolves fixtures through Fixture Ingestion identities, appends price observations rather than overwriting them, detects market movement, and writes audit/outbox records in the same transaction. Read-only history, latest odds, fixture odds, market odds, bookmaker, market, and movement endpoints are available under `/api/v1/market-data`.

See [the Market Data module guide](app/modules/market_data/README.md) for the reference payload, movement rules, and second-provider integration process.

## Database migrations

Alembic includes the canonical Sports Domain, Fixture Ingestion, Market Data & Odds, Statistics, Feature Store, Research Engine, Probability Engine, and Consensus Engine migrations. Future bounded modules must add their own reviewed migrations rather than modifying historical revisions.

```powershell
alembic upgrade head
alembic revision --autogenerate -m "describe the change"
```

Run migration commands from `backend/`. Review every generated migration before applying it.

## Feature Store

The Feature Store reads only canonical Sports, Statistics, and Market Data records. It never reads provider payloads. `POST /api/v1/feature-store/generations` generates a deterministic, immutable snapshot for a fixture and an explicit `as_of` timestamp; it requires `research:execute`. Read APIs under `/api/v1/feature-store` require `data:read` and expose Feature Set metadata, values, lineage, and validation evidence.

See [the Feature Store module guide](app/modules/feature_store/README.md) for versions, generators, historical regeneration, and retrieval filters.

## Research Engine

The Research Engine accepts only a specific Feature Set version and materializes the selected Feature Store values into an immutable dataset snapshot. Experiments run descriptive, distribution, correlation, or exploratory significance analyses against those frozen rows, store the exact parameters and random seed, and write immutable lineage and validation evidence. It contains no predictive model training or recommendation logic. Write operations require `research:execute`; all read APIs under `/api/v1/research` require `data:read`.

See [the Research Engine module guide](app/modules/research/README.md) for the experiment lifecycle, hypothesis evidence, reproducibility guarantees, and API inventory.

## Probability Engine

The Probability Engine consumes only immutable Research datasets and experiments. It supports registry-selected transparent baseline models, versioned Platt/isotonic/temperature calibration, immutable fixture estimates, evaluation metrics, and complete replay lineage. It produces no recommendation, stake, or betting decision. Execution under `/api/v1/probability` requires `probability:execute`; evidence reads require `data:read`.

See [the Probability Engine module guide](app/modules/probability/README.md) for the inference, calibration, evaluation, ensemble, and validation contracts.

## Consensus Engine

The Consensus Engine combines compatible immutable Probability outputs through registry-selected strategies and records confidence, disagreement, completeness, validation, and full lineage. It does not compare odds or create any recommendation. Writes under `/api/v1/consensus` require `consensus:execute`; evidence reads require `data:read`.

See [the Consensus Engine module guide](app/modules/consensus/README.md) for strategy, confidence, disagreement, and reproducibility details.

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
