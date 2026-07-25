# Transactional Outbox Worker

Run locally with:

```powershell
cd backend
python -m app.workers.main
```

The worker polls the existing Fixture Ingestion, Market Data, and Statistics outbox tables. It claims ready rows with PostgreSQL `FOR UPDATE SKIP LOCKED`, records a time-bounded lease, increments attempts, and sends a local `LoggingEventSink` delivery confirmation.

Successful events are marked `published_at`. Failures receive exponential backoff. After `TITAN_OUTBOX_MAX_ATTEMPTS`, the original outbox row is retained with `dead_lettered_at` and `last_error`; it is no longer polled. Events are never deleted.

Delivery is **at-least-once**. `event_key` is unique in every source outbox and is supplied as the consumer idempotency key. A future in-process subscriber or external transport must deduplicate on that value.

Worker metrics are emitted through the worker-local Prometheus registry: claimed, delivered, retried, dead-lettered, lease-conflict, and per-poll pending counts, each labelled by bounded context.
