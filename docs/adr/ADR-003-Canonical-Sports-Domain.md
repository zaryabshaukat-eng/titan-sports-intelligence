# ADR-003 — Provider-Neutral Canonical Sports Domain

**Status:** Accepted  
**Date:** 2026-07-15

## Context

TITAN will eventually receive sports data from multiple providers. Provider-specific schemas would couple downstream research and intelligence to source formats and undermine reproducibility.

## Decision

Represent countries, leagues, competitions, seasons, teams, venues, timezones, fixtures, statuses, and officials using a canonical internal model. Provider identifiers and raw payloads belong to the future ingestion boundary, not the Sports Domain.

## Consequences

- Downstream modules depend on stable TITAN identities rather than provider terminology.
- Ingestion adapters must normalize external feeds before publishing canonical records.
- Fixture status and official assignments are modeled as canonical, auditable relationships.
