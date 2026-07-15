# ADR-002 — PostgreSQL as Authoritative Relational Store

**Status:** Accepted  
**Date:** 2026-07-15

## Context

TITAN requires strong referential integrity, transactional migrations, time-aware querying, audit-friendly history, and a reliable system of record.

## Decision

Use PostgreSQL as the authoritative relational database, accessed through SQLAlchemy 2.x and migrated through Alembic. Redis is restricted to transient operational concerns.

## Consequences

- Core entities gain enforceable foreign keys, check constraints, and indexes.
- Schema changes require reviewed append-only Alembic migrations.
- Large immutable files and artifacts remain outside PostgreSQL in object storage when introduced.
