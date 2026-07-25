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
| [phase-2-architecture-review.md](phase-2-architecture-review.md) | Original Phase 2 architecture blueprint and governance additions |

## Reserved future documents

The following numbers are reserved for their respective implementation milestones and should be created when that module begins work, not as empty placeholders:

- `006-feature-store.md`
- `007-research-engine.md`
- `008-probability-engine.md`
- `009-consensus-engine.md`
- `010-risk-engine.md`
- `011-explainability.md`
