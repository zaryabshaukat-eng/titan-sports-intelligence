# ADR-004 — Use a Transactional Outbox for Fixture Ingestion Events

- **Status:** Accepted
- **Date:** 2026-07-15
- **Decision:** Store fixture-ingestion domain events in PostgreSQL in the same transaction as canonical writes and audit records.

## Context

Fixture ingestion must be reproducible and reliable. Publishing directly to a broker after database updates risks losing events on process failure; publishing first risks emitting events for data that never commits.

## Decision

The ingestion pipeline writes an `ingestion_outbox_events` row atomically with the raw payload, canonical mutation, and audit record. A future background worker will deliver unpublished rows and mark them published only after acknowledgement.

## Consequences

- Event publication is reliable across request/process failures.
- This phase has no broker dependency and does not claim delivery semantics it has not implemented.
- The database needs an outbox-retention and delivery-monitoring policy when workers are introduced.
