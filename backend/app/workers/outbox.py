"""Local, async, at-least-once delivery worker for TITAN transactional outboxes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any, Protocol
from uuid import UUID, uuid4

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from sqlalchemy import Select, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.modules.ingestion.models import IngestionOutboxEvent
from app.modules.market_data.models import MarketDataOutboxEvent
from app.modules.statistics.models import StatisticsOutboxEvent

logger = get_logger(__name__)
OutboxModel = type[IngestionOutboxEvent] | type[MarketDataOutboxEvent] | type[StatisticsOutboxEvent]


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    """Delivery-safe event envelope; `event_key` is the consumer idempotency key."""

    context: str
    event_id: UUID
    event_key: str
    event_type: str
    payload: dict[str, object]
    occurred_at: datetime
    attempts: int


class EventSink(Protocol):
    """Local delivery boundary; future transports must deduplicate by `event_key`."""

    async def deliver(self, message: OutboxMessage) -> None:
        """Deliver one event or raise a recoverable delivery exception."""


class LoggingEventSink:
    """Default local sink that confirms delivery by structured log, without exposing payloads."""

    async def deliver(self, message: OutboxMessage) -> None:
        logger.info(
            "outbox.event_delivered",
            extra={
                "extra_fields": {
                    "outbox_context": message.context,
                    "event_id": str(message.event_id),
                    "event_key": message.event_key,
                    "event_type": message.event_type,
                    "attempt": message.attempts,
                }
            },
        )


@dataclass(slots=True)
class OutboxWorkerMetrics:
    """Worker-local Prometheus collectors, isolated to make worker tests deterministic."""

    registry: CollectorRegistry = field(default_factory=CollectorRegistry)
    claimed: Counter = field(init=False)
    delivered: Counter = field(init=False)
    retried: Counter = field(init=False)
    dead_lettered: Counter = field(init=False)
    lease_conflicts: Counter = field(init=False)
    pending: Gauge = field(init=False)
    processing_duration_seconds: Histogram = field(init=False)

    def __post_init__(self) -> None:
        labels = ("context",)
        self.claimed = Counter(
            "titan_outbox_claimed_total", "Claimed outbox events.", labels, registry=self.registry
        )
        self.delivered = Counter(
            "titan_outbox_delivered_total",
            "Delivered outbox events.",
            labels,
            registry=self.registry,
        )
        self.retried = Counter(
            "titan_outbox_retried_total", "Retried outbox events.", labels, registry=self.registry
        )
        self.dead_lettered = Counter(
            "titan_outbox_dead_lettered_total",
            "Dead-lettered outbox events.",
            labels,
            registry=self.registry,
        )
        self.lease_conflicts = Counter(
            "titan_outbox_lease_conflicts_total",
            "Lost outbox leases.",
            labels,
            registry=self.registry,
        )
        self.pending = Gauge(
            "titan_outbox_pending",
            "Events currently claimed in a poll.",
            labels,
            registry=self.registry,
        )
        self.processing_duration_seconds = Histogram(
            "titan_outbox_processing_duration_seconds",
            "Duration of one outbox dispatch attempt.",
            labels,
            registry=self.registry,
        )


class TransactionalOutboxWorker:
    """Claim, deliver, and acknowledge all module-owned outbox tables with DB leases."""

    _sources: tuple[tuple[str, OutboxModel, str], ...] = (
        ("fixture_ingestion", IngestionOutboxEvent, "occurred_at"),
        ("market_data", MarketDataOutboxEvent, "occurred_at"),
        ("statistics", StatisticsOutboxEvent, "created_at"),
    )

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        sink: EventSink | None = None,
        *,
        batch_size: int = 100,
        lease_seconds: int = 30,
        max_attempts: int = 8,
        retry_initial_seconds: float = 1.0,
        retry_max_seconds: float = 300.0,
        retry_backoff_multiplier: float = 2.0,
        shutdown_timeout_seconds: float = 30.0,
        metrics: OutboxWorkerMetrics | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._sink = sink or LoggingEventSink()
        self._batch_size = batch_size
        self._lease_seconds = lease_seconds
        self._max_attempts = max_attempts
        self._retry_initial_seconds = retry_initial_seconds
        self._retry_max_seconds = retry_max_seconds
        self._retry_backoff_multiplier = retry_backoff_multiplier
        self._shutdown_timeout_seconds = shutdown_timeout_seconds
        self._metrics = metrics or OutboxWorkerMetrics()
        self._now = now or (lambda: datetime.now(UTC))
        self.worker_id = str(uuid4())

    async def run_once(self) -> int:
        """Process one bounded batch from each module outbox and return delivered count."""
        delivered = 0
        for context, model, occurred_column in self._sources:
            claimed = await self._claim(context, model, occurred_column)
            self._metrics.pending.labels(context=context).set(len(claimed))
            for message in claimed:
                delivered += await self._deliver(message, model)
        return delivered

    async def run_forever(self, poll_interval_seconds: float, stop_event: asyncio.Event) -> None:
        """Poll until shutdown, draining an active batch within the configured timeout."""
        while not stop_event.is_set():
            poll_task = asyncio.create_task(self.run_once())
            shutdown_task = asyncio.create_task(stop_event.wait())
            done, _ = await asyncio.wait(
                {poll_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
            )
            if shutdown_task in done:
                if not poll_task.done():
                    try:
                        await asyncio.wait_for(
                            asyncio.shield(poll_task), timeout=self._shutdown_timeout_seconds
                        )
                    except TimeoutError:
                        poll_task.cancel()
                        with suppress(asyncio.CancelledError):
                            await poll_task
                        logger.warning(
                            "outbox.shutdown_timeout",
                            extra={"extra_fields": {"worker_id": self.worker_id}},
                        )
                return
            shutdown_task.cancel()
            with suppress(asyncio.CancelledError):
                await shutdown_task
            delivered = poll_task.result()
            if delivered:
                continue
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_seconds)
            except TimeoutError:
                continue

    async def _claim(
        self, context: str, model: OutboxModel, occurred_column: str
    ) -> list[OutboxMessage]:
        now = self._now()
        lease_expires_at = now + timedelta(seconds=self._lease_seconds)
        next_attempt_at = model.next_attempt_at
        lease_expires = model.lease_expires_at
        statement: Select[tuple[Any]] = (
            select(model)
            .where(
                model.published_at.is_(None),
                model.dead_lettered_at.is_(None),
                next_attempt_at <= now,
                or_(lease_expires.is_(None), lease_expires <= now),
            )
            .order_by(next_attempt_at, getattr(model, occurred_column))
            .with_for_update(skip_locked=True)
            .limit(self._batch_size)
        )
        async with self._session_factory() as session:
            events = list((await session.scalars(statement)).all())
            for event in events:
                event.lease_owner = self.worker_id
                event.lease_expires_at = lease_expires_at
                event.delivery_attempts = (event.delivery_attempts or 0) + 1
            await session.commit()
        self._metrics.claimed.labels(context=context).inc(len(events))
        return [
            OutboxMessage(
                context=context,
                event_id=event.id,
                event_key=event.event_key,
                event_type=getattr(event.event_type, "value", str(event.event_type)),
                payload=event.payload,
                occurred_at=getattr(event, occurred_column),
                attempts=event.delivery_attempts,
            )
            for event in events
        ]

    async def _deliver(self, message: OutboxMessage, model: OutboxModel) -> int:
        started = perf_counter()
        try:
            await self._sink.deliver(message)
        except Exception as exc:  # Sink adapters intentionally define their own recoverable errors.
            duration = perf_counter() - started
            self._metrics.processing_duration_seconds.labels(context=message.context).observe(duration)
            await self._record_failure(message, model, exc, duration)
            return 0
        duration = perf_counter() - started
        self._metrics.processing_duration_seconds.labels(context=message.context).observe(duration)
        acknowledged = await self._acknowledge(message, model)
        if acknowledged:
            logger.info(
                "outbox.event_published",
                extra={
                    "extra_fields": {
                        "worker_id": self.worker_id,
                        "event_id": str(message.event_id),
                        "event_type": message.event_type,
                        "attempt": message.attempts,
                        "duration_ms": round(duration * 1000, 3),
                    }
                },
            )
        return 1 if acknowledged else 0

    async def _acknowledge(self, message: OutboxMessage, model: OutboxModel) -> bool:
        now = self._now()
        async with self._session_factory() as session:
            result = await session.execute(
                update(model)
                .where(
                    model.id == message.event_id,
                    model.lease_owner == self.worker_id,
                    model.published_at.is_(None),
                )
                .values(
                    published_at=now,
                    lease_owner=None,
                    lease_expires_at=None,
                    last_error=None,
                )
            )
            await session.commit()
        if result.rowcount != 1:
            self._metrics.lease_conflicts.labels(context=message.context).inc()
            logger.warning(
                "outbox.lease_lost_before_ack",
                extra={
                    "extra_fields": {
                        "worker_id": self.worker_id,
                        "event_id": str(message.event_id),
                        "event_type": message.event_type,
                        "attempt": message.attempts,
                        "event_key": message.event_key,
                        "context": message.context,
                    }
                },
            )
            return False
        self._metrics.delivered.labels(context=message.context).inc()
        return True

    async def _record_failure(
        self, message: OutboxMessage, model: OutboxModel, exc: Exception, duration_seconds: float
    ) -> None:
        now = self._now()
        error = f"{exc.__class__.__name__}: {exc}"[:2000]
        dead_letter = message.attempts >= self._max_attempts
        values: dict[str, object] = {
            "lease_owner": None,
            "lease_expires_at": None,
            "last_error": error,
        }
        if dead_letter:
            values["dead_lettered_at"] = now
        else:
            delay = min(
                self._retry_initial_seconds
                * (self._retry_backoff_multiplier ** max(message.attempts - 1, 0)),
                self._retry_max_seconds,
            )
            values["next_attempt_at"] = now + timedelta(seconds=delay)
        async with self._session_factory() as session:
            result = await session.execute(
                update(model)
                .where(model.id == message.event_id, model.lease_owner == self.worker_id)
                .values(**values)
            )
            await session.commit()
        if result.rowcount != 1:
            self._metrics.lease_conflicts.labels(context=message.context).inc()
            return
        if dead_letter:
            self._metrics.dead_lettered.labels(context=message.context).inc()
            logger.error(
                "outbox.event_dead_lettered",
                extra={
                    "extra_fields": {
                        "event_key": message.event_key,
                        "worker_id": self.worker_id,
                        "event_id": str(message.event_id),
                        "event_type": message.event_type,
                        "context": message.context,
                        "attempt": message.attempts,
                        "duration_ms": round(duration_seconds * 1000, 3),
                        "error": error,
                    }
                },
            )
        else:
            self._metrics.retried.labels(context=message.context).inc()
            logger.warning(
                "outbox.event_retry_scheduled",
                extra={
                    "extra_fields": {
                        "event_key": message.event_key,
                        "worker_id": self.worker_id,
                        "event_id": str(message.event_id),
                        "event_type": message.event_type,
                        "context": message.context,
                        "attempt": message.attempts,
                        "duration_ms": round(duration_seconds * 1000, 3),
                        "error": error,
                    }
                },
            )
