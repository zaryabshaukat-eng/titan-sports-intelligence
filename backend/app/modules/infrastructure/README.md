# Infrastructure & Scaling

Infrastructure provides explicit Redis cache isolation, best-effort distributed locks, bounded retry support, and protected operational health/status endpoints. Redis failures degrade safely to cache misses and unavailable locks; business truth is never cached as an authority.

Existing transactional outbox workers remain the current queue/delivery engine. This module adds abstractions without changing business bounded contexts.
