# 001 — TITAN OS System Overview

**Status:** Implemented through Phase 2.7

**Last updated:** 2026-07-26

TITAN OS is an evidence-driven Sports Intelligence Operating System. The completed frontend remains the presentation layer; the backend is a modular FastAPI core designed to evolve without premature microservice complexity.

## Current platform shape

```text
React 19 + TanStack Start frontend
              |
      /api/v1 FastAPI API
              |
  Modular TITAN Core backend
    - Configuration and security foundation
    - PostgreSQL and Redis clients
    - Alembic migrations
    - Structured logging and metrics
    - Canonical Sports Domain
    - Provider-neutral ingestion and immutable historical data
    - Versioned Feature Store and deterministic offline generators
    - Immutable Research dataset snapshots and statistical experiments
    - Calibrated Probability Engine baseline inference and evaluation evidence
    - Consensus probabilities with confidence and disagreement evidence
```

## Design boundaries

- The frontend does not access the database directly.
- Sports entities are provider-neutral and contain no ingestion payload fields.
- Public read APIs are versioned under `/api/v1`.
- Feature generation is implemented against canonical data only. Research and Probability use frozen artifacts; recommendation publication remains outside the currently implemented scope.
- The modular-monolith boundary is intentional: modules have explicit ownership and can be extracted later only when operational evidence supports it.

## Completed milestones

| Milestone | Outcome |
| --- | --- |
| Phase 1 | React/TanStack presentation application |
| Phase 2.2 | FastAPI, configuration, database/Redis clients, migrations, observability, Docker foundation |
| Phase 2.3.1 | Canonical Sports models, migration, repositories, and read-only API |
| Phase 2.3.2–2.3.8 | Fixture/Market/Statistics ingestion, transactional outbox, identity, observability, and production hardening |
| Phase 2.4 | Versioned Feature Store, immutable feature values, lineage, validation, deterministic generators, and read APIs |
| Phase 2.5 | Immutable Research datasets, reproducible statistical experiments, hypotheses, lineage, validation, and APIs |
| Phase 2.6 | Versioned baseline probability models, calibration, immutable estimates, evaluation, lineage, and APIs |
| Phase 2.7 | Immutable consensus strategies, evidence metrics, lineage, validation, and APIs |
