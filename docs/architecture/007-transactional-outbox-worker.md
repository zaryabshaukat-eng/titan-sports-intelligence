# Transactional Outbox Worker

The local worker is TITAN's bridge from committed domain transactions to future event-driven processing. It consumes only the existing outbox tables and does not require Kafka or RabbitMQ.

Each poll selects ready, unpublished, non-dead-lettered events using PostgreSQL row locks with `SKIP LOCKED`. The selected rows receive a worker ID, lease expiry, and incremented attempt count in a committed claim transaction. Acknowledgement and failure updates require that same lease owner, preventing stale workers from acknowledging another worker's event.

Failures use capped exponential backoff. Exhausted events remain as first-class operational evidence with `dead_lettered_at` and a bounded `last_error`. The worker does not delete events.

Delivery is at-least-once by design. Every consumer must use the existing unique `event_key` for idempotency.

## Runtime behavior

`TransactionalOutboxWorker` polls each bounded-context outbox in batches. Its claim query uses `FOR UPDATE SKIP LOCKED`, records the unique worker ID and lease expiry, and increments the delivery attempt before dispatch. Acknowledgement and failure updates require the same lease owner, so a stale worker cannot publish or reschedule an event claimed by another worker. Expired leases become eligible for a later poll.

The `EventSink` protocol is the dispatcher boundary. `LoggingEventSink` is the local implementation; a future transport must implement only `deliver(message)` and deduplicate with `event_key`.

Shutdown stops new polls and waits for the active serial batch up to `TITAN_OUTBOX_SHUTDOWN_TIMEOUT_SECONDS`; on timeout it cancels the in-process task while the database lease safely makes the event available again after expiry.

## Configuration and metrics

Configuration is environment-backed: `TITAN_OUTBOX_POLL_INTERVAL_SECONDS`, `TITAN_OUTBOX_BATCH_SIZE`, `TITAN_OUTBOX_LEASE_SECONDS`, `TITAN_OUTBOX_MAX_ATTEMPTS`, `TITAN_OUTBOX_RETRY_INITIAL_SECONDS`, `TITAN_OUTBOX_RETRY_MAX_SECONDS`, `TITAN_OUTBOX_RETRY_BACKOFF_MULTIPLIER`, and `TITAN_OUTBOX_SHUTDOWN_TIMEOUT_SECONDS`.

The worker exposes bounded-context metrics for claimed events, published events (whose Prometheus rate is throughput), retry count, dead-letter count, lease conflicts, pending claimed rows, and `titan_outbox_processing_duration_seconds`. Structured delivery logs include the worker ID, event ID/type, attempt, duration, and failure reason when applicable; request/trace correlation fields are attached automatically when present.
