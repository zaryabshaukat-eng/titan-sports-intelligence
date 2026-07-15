# TITAN OS Architecture Documentation

This directory contains long-lived technical architecture documentation. Documents are numbered in implementation order and updated through reviewed commits rather than informal chat history.

## Current documents

| Document | Scope |
| --- | --- |
| [001-system-overview.md](001-system-overview.md) | Current platform layers, boundaries, and delivery state |
| [002-database.md](002-database.md) | PostgreSQL, Redis, migrations, and persistence standards |
| [003-sports-domain.md](003-sports-domain.md) | Canonical provider-neutral Sports Domain |
| [004-ingestion.md](004-ingestion.md) | Provider-neutral fixture ingestion, audit, and transactional outbox |
| [phase-2-architecture-review.md](phase-2-architecture-review.md) | Original Phase 2 architecture blueprint and governance additions |

## Reserved future documents

The following numbers are reserved for their respective implementation milestones and should be created when that module begins work, not as empty placeholders:

- `005-feature-store.md`
- `006-research-engine.md`
- `007-probability-engine.md`
- `008-consensus-engine.md`
- `009-risk-engine.md`
- `010-explainability.md`
