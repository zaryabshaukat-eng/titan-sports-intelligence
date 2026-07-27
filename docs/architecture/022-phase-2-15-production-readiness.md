# Phase 2.15 Production Readiness Report

**Status:** Local validation complete; external release evidence pending.

## Type-Safety Hardening completed

The dedicated, behavior-preserving type-safety sub-phase is complete.

- `python -m mypy app --ignore-missing-imports --follow-imports=skip` succeeds for all 286 backend source files.
- Ruff lint and formatting checks succeed.
- The final local regression suite completed with **102 passed, 5 skipped** tests. The five skips are the documented PostgreSQL environment requirement.
- No business logic, algorithms, database schemas, API contracts, frontend behavior, or model behavior changed as part of the typing work.

No further annotation-only refactors are authorized under Phase 2.15.

## Local test and coverage result

The final local suite completed with **102 passed, 5 skipped, and 1 dependency deprecation warning**. The generated coverage report records **78% total line coverage**. The skipped cases are exclusively the documented PostgreSQL environment tests. The lower-covered areas are primarily live persistence adapters, service paths that require a database, and worker process entry points; the report does not establish production load behavior. Coverage is published by the CI workflow and must be reviewed together with the PostgreSQL integration result before release promotion.

## Security hardening assessment

The existing production configuration fails closed for the development secret, interactive documentation, wildcard or localhost CORS origins, the development identity provider, and missing JWT credentials. Authentication uses strict HS256 verification with issuer, audience, expiry, and optional not-before validation; authorization is permission-based and protected routes are covered by contract tests. Baseline browser security headers are applied to all responses.

No code-level critical security blocker was found. The following remain deployment controls and must be verified before release:

- configure an explicit `TITAN_TRUSTED_HOSTS` allow-list or enforce equivalent host-header policy at the trusted reverse proxy;
- inject production secrets only through the deployment secret store, never Compose defaults or source-controlled environment files;
- use the JWT provider (or another approved production provider), not development credentials; and
- place a shared gateway or distributed rate limiter in front of horizontally scaled API instances, because the current local limiter is intentionally process-scoped.

## PostgreSQL environment validation requirement

Five integration tests are intentionally skipped locally when `TITAN_TEST_DATABASE_URL` is unavailable:

- database connectivity;
- fixture-ingestion integration;
- market-data integration;
- statistics integration; and
- live migration validation.

This is an **environment validation requirement**, not a code defect. Before release promotion, CI or staging must supply an isolated PostgreSQL database through `TITAN_TEST_DATABASE_URL`, run Alembic migration setup, and execute these tests successfully. The repository's `postgresql-integration` GitHub Actions job defines that target environment.

## Performance, concurrency, and migration validation

The static validation path is healthy: the focused repository and migration regression suite passed (**24 passed**), and Alembic offline SQL generation completed for `upgrade head`, `downgrade head:base`, and a second `upgrade head`. This verifies migration ordering and downgrade SQL generation without mutating a database.

The live performance and concurrency claims must not be inferred from those results. Docker is unavailable in the current workstation and no PostgreSQL test URL is configured, so the following are **release-evidence gates** to execute in CI or staging against an isolated, production-like database:

- capture `EXPLAIN (ANALYZE, BUFFERS)` for latest-fixture, latest-odds, and latest-statistics queries, confirming the intended composite indexes are selected;
- measure p50, p95, and p99 request latency, query count, and memory for representative read and ingestion batches;
- run concurrent duplicate-payload ingestion, outbox lease-expiry/retry, and worker-claim race tests;
- verify worker concurrency and queue-drain throughput against the operating service-level objectives; and
- demonstrate rate-limit behavior across multiple API replicas, because the in-process limiter is not a shared distributed policy.

The implementation already has targeted repository, reliability, and outbox tests; these gates provide the production-scale evidence that a local unit suite cannot truthfully establish.

## Disaster recovery, rollback, and CI parity

Recovery and failed-migration runbooks exist in `docs/operations/runbooks.md`; deployment and rollback steps are defined in `docs/operations/v0.3.0-release-validation.md`. Docker Compose gates API and worker startup on a successful migration job. The GitHub Actions workflow covers linting, formatting, mypy, the test suite with coverage, offline Alembic round-trips, Compose configuration, container build, and a dedicated PostgreSQL/Redis integration job.

Before a production release candidate, the release operator must record evidence for:

- a backup-and-restore drill to a separate PostgreSQL instance, followed by migration and `/ready` verification;
- a rollback drill that rolls back the application image first and uses a database downgrade only when the reviewed migration and verified backup make it safe;
- a successful CI run for both workflow jobs, including the five PostgreSQL integration tests; and
- a containerized startup/health-check validation with production-equivalent secrets, host policy, TLS ingress, and alert routing.

These are environment execution gates rather than application-code defects. No behavior-changing hardening change is justified until the results identify a concrete failure.

## Remaining workstreams

1. Execute the PostgreSQL, Docker, load, concurrency, recovery, and CI evidence gates in CI or staging.
2. Assess any resulting failure and make only an approved, backward-compatible remediation.
3. Publish the final Production Readiness and Architecture Freeze reports.

No public production release may be approved until the PostgreSQL environment validation requirement and all applicable Phase 2.15 release gates have evidence.
