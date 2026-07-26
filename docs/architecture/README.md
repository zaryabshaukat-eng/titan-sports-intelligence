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
| [010-feature-store.md](010-feature-store.md) | Versioned, reproducible Feature Store and deterministic canonical-data generators |
| [011-research-engine.md](011-research-engine.md) | Immutable Feature Store dataset snapshots and reproducible statistical experiments |
| [013-probability-engine.md](013-probability-engine.md) | Calibrated, immutable probability runs, outputs, evaluation, and lineage |
| [014-consensus-engine.md](014-consensus-engine.md) | Evidence-only combination, confidence, disagreement, and lineage |
| [015-risk-engine.md](015-risk-engine.md) | Immutable uncertainty, stability, calibration, agreement, and data-quality assessments |
| [016-explainability.md](016-explainability.md) | Immutable contributions, evidence, reasoning chains, confidence, and lineage |
| [017-backtesting-simulation.md](017-backtesting-simulation.md) | Deterministic historical replay, scenarios, leakage controls, metrics, and lineage |
| [018-continuous-evaluation.md](018-continuous-evaluation.md) | Append-only analytical health, drift, quality, alerts, and lineage monitoring |
| [019-continuous-improvement.md](019-continuous-improvement.md) | Advisory-only improvement evidence and human-controlled promotion decisions |
| [phase-2-architecture-review.md](phase-2-architecture-review.md) | Original Phase 2 architecture blueprint and governance additions |
| [012-platform-freeze-v0.3.0.md](012-platform-freeze-v0.3.0.md) | v0.3.0 architecture audit, scores, release gates, and freeze decision |

## Reserved future documents

The following numbers are reserved for their respective implementation milestones and should be created when that module begins work, not as empty placeholders:
