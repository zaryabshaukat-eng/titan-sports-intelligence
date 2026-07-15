# ADR-001 — Modular Monolith

**Status:** Accepted  
**Date:** 2026-07-15

## Context

TITAN requires many independently understandable domains but does not yet have the operational scale, team topology, or deployment needs that justify distributed microservices.

## Decision

Build TITAN Core as a modular FastAPI application with explicit bounded-context packages, versioned internal contracts, and independently testable persistence boundaries.

## Consequences

- Development and operations remain straightforward in early phases.
- Modules can be extracted later based on measured operational need.
- Cross-module coupling must remain explicit; convenience imports and shared mutable domain state are prohibited.
