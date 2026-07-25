# ADR-005 — Preserve Immutable Odds History

- **Status:** Accepted
- **Date:** 2026-07-25
- **Decision:** Store every changed decimal price as a new odds snapshot and derive movements as append-only records.

## Context

Replacing an odds value destroys the evidence required to audit future analysis. TITAN needs opening/closing prices, movement direction, provider comparisons, and historical replay without trusting an external provider to retain old responses.

## Decision

`OddsSnapshot` rows are immutable and retain source-provider, bookmaker, fixture, market, selection, observation time, raw payload, run, and checksum provenance. Repeated unchanged prices are audited but do not create duplicate snapshots. `OddsMovement` records explain price and market lifecycle changes without changing snapshots.

## Consequences

- Storage grows with meaningful price changes and needs time-based retention/capacity monitoring.
- Current/latest views are derived from history rather than written as mutable truth.
- Future consensus and research modules can replay evidence without modifying Market Data records.
