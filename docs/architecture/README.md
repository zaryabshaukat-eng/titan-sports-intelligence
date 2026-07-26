# TITAN OS Architecture Documentation

This directory contains long-lived technical architecture documentation. Documents are numbered in implementation order and updated through reviewed commits rather than informal chat history.

## Current documents

| Document | Scope |
| --- | --- |
| [001-system-overview.md](001-system-overview.md) | Current platform layers, boundaries, and delivery state |
| [002-database.md](002-database.md) | PostgreSQL, Redis, migrations, and persistence standards |
| [003-sports-domain.md](003-sports-domain.md) | Canonical provider-neutral Sports Domain |
| [004-ingestion.md](004-ingestion.md) | Provider-neutral fixture ingestion, audit, and transactional outbox |
| [005-market-data.md](005-market-data.md) | Immutable odds history, market lifecycle, movement tracking, and audit |
| [006-statistics-ingestion.md](006-statistics-ingestion.md) | Provider-neutral, immutable statistics history and replayability |
| [007-transactional-outbox-worker.md](007-transactional-outbox-worker.md) | Local at-least-once event delivery, leasing, retries, and dead letters |
| [008-identity-foundation.md](008-identity-foundation.md) | Pluggable identity, JWT validation, roles, and permissions |
| [009-observability.md](009-observability.md) | Health, readiness, metrics, correlation, and operational thresholds |
| [phase-2-architecture-review.md](phase-2-architecture-review.md) | Original Phase 2 architecture blueprint and governance additions |
| [012-platform-freeze-v0.3.0.md](012-platform-freeze-v0.3.0.md) | v0.3.0 architecture audit, scores, release gates, and freeze decision |

## Reserved future documents

The following numbers are reserved for their respective implementation milestones and should be created when that module begins work, not as empty placeholders:

- `010-feature-store.md`
- `011-research-engine.md`
- `013-probability-engine.md`
- `014-consensus-engine.md`
- `015-risk-engine.md`
- `016-explainability.md`
