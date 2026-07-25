# Transactional Outbox Worker

The local worker is TITAN's bridge from committed domain transactions to future event-driven processing. It consumes only the existing outbox tables and does not require Kafka or RabbitMQ.

Each poll selects ready, unpublished, non-dead-lettered events using PostgreSQL row locks with `SKIP LOCKED`. The selected rows receive a worker ID, lease expiry, and incremented attempt count in a committed claim transaction. Acknowledgement and failure updates require that same lease owner, preventing stale workers from acknowledging another worker's event.

Failures use capped exponential backoff. Exhausted events remain as first-class operational evidence with `dead_lettered_at` and a bounded `last_error`. The worker does not delete events.

Delivery is at-least-once by design. Every consumer must use the existing unique `event_key` for idempotency.
