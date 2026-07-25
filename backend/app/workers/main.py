"""Runnable local worker entry point: `python -m app.workers.main`."""

from __future__ import annotations

import asyncio
import signal
from contextlib import suppress

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.workers.outbox import TransactionalOutboxWorker


async def main() -> None:
    """Start the local outbox worker and dispose its independent connection pool on shutdown."""
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        # Windows event loops do not provide Unix signal-handler registration.
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    worker = TransactionalOutboxWorker(
        async_sessionmaker(engine, expire_on_commit=False),
        batch_size=settings.outbox_batch_size,
        lease_seconds=settings.outbox_lease_seconds,
        max_attempts=settings.outbox_max_attempts,
        retry_initial_seconds=settings.outbox_retry_initial_seconds,
        retry_max_seconds=settings.outbox_retry_max_seconds,
        retry_backoff_multiplier=settings.outbox_retry_backoff_multiplier,
        shutdown_timeout_seconds=settings.outbox_shutdown_timeout_seconds,
    )
    try:
        await worker.run_forever(settings.outbox_poll_interval_seconds, stop_event)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
