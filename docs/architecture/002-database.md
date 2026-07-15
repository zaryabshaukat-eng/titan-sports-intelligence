# 002 — Database Architecture

**Status:** Implemented foundation and Sports Domain schema  
**Last updated:** 2026-07-15

## Storage roles

| Store | Role |
| --- | --- |
| PostgreSQL | Authoritative relational records, constraints, metadata, migrations, and audit-friendly timestamps |
| Redis | Cache, rate-limiting, idempotency, and future job coordination; never the permanent source of truth |
| Object storage | Reserved for immutable raw payloads, model artifacts, feature matrices, evidence packages, and reports |

## Persistence standards

- PostgreSQL UUID primary keys are application assigned.
- All canonical entities retain `created_at` and `updated_at` timestamps.
- Mutable master data uses `deleted_at` soft deletion when historical preservation matters.
- Fixtures are never soft deleted. Cancellation and abandonment are represented by canonical status and status history.
- Database integrity lives in foreign keys, check constraints, unique constraints, and indexed query dimensions.
- Alembic migrations are append-only historical artifacts. Existing migrations must not be edited after deployment.

## Current migration

`20260715_0001_canonical_sports_domain` creates the canonical Sports schema, controlled PostgreSQL enums, indexes, and seeded fixture-status taxonomy.

Run migrations from `backend/`:

```powershell
alembic upgrade head
```
