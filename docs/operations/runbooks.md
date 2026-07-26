# TITAN OS Operational Runbooks

## Database recovery

Declare an incident, stop writers, restore the latest verified PostgreSQL backup to a new instance, run `alembic upgrade head`, verify `/ready`, then switch application and worker connection strings. Preserve the failed database for forensic review.

## Failed migration

Stop API/worker rollout, capture Alembic revision and PostgreSQL logs, and restore from backup if the migration is not explicitly reversible. Never run a downgrade against production without a tested backup and a reviewed rollback plan.

## Outbox backlog or worker failure

Check `titan_outbox_backlog`, retries, dead-letter count, worker logs, and Redis/PostgreSQL availability. Restart the worker only after recording the incident; leases recover abandoned rows automatically. Investigate dead-letter event keys and raw/audit evidence before replay.

## Redis or provider outage

Use `/ready` to isolate Redis/database/identity failures. Keep historical data immutable; pause provider delivery if freshness falls below the operating SLO and resume with idempotent ingestion after recovery.

## Authentication failure spike

Review provider, issuer/audience configuration, clock skew, ingress logs, and credential rotation events. Do not log credentials or JWT contents. Rate-limit or block abusive sources at the network edge.
