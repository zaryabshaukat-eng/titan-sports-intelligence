# TITAN OS Architecture Decision Records

Architecture Decision Records (ADRs) preserve the context, decision, alternatives, and consequences of material engineering choices. ADRs are immutable once accepted; later decisions supersede earlier records rather than rewriting them.

## Accepted ADRs

| ADR | Decision |
| --- | --- |
| [ADR-001](ADR-001-Modular-Monolith.md) | Begin TITAN Core as a modular monolith |
| [ADR-002](ADR-002-PostgreSQL.md) | Use PostgreSQL as the authoritative relational store |
| [ADR-003](ADR-003-Canonical-Sports-Domain.md) | Use a provider-neutral canonical Sports Domain |
| [ADR-004](ADR-004-Transactional-Outbox.md) | Use a transactional outbox for fixture ingestion events |
| [ADR-005](ADR-005-Immutable-Odds-History.md) | Preserve immutable odds history and append-only movement evidence |
