"""Unit coverage for local transactional-outbox delivery behavior."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from app.modules.ingestion.models import IngestionOutboxEvent
from app.workers.outbox import EventSink, OutboxMessage, TransactionalOutboxWorker


class _SuccessfulSink(EventSink):
    def __init__(self) -> None:
        self.messages: list[OutboxMessage] = []

    async def deliver(self, message: OutboxMessage) -> None:
        self.messages.append(message)


class _FailingSink(EventSink):
    async def deliver(self, message: OutboxMessage) -> None:
        raise RuntimeError("temporary sink failure")


def _message() -> OutboxMessage:
    return OutboxMessage(
        context="statistics",
        event_id=uuid4(),
        event_key="statistics:test:1",
        event_type="StatisticsIngested",
        payload={"snapshot_id": "example"},
        occurred_at=datetime.now(UTC),
        attempts=1,
    )


def test_successful_delivery_acknowledges_exactly_the_leased_event() -> None:
    async def run() -> None:
        sink = _SuccessfulSink()
        worker = TransactionalOutboxWorker(AsyncMock(), sink)
        worker._acknowledge = AsyncMock(return_value=True)

        delivered = await worker._deliver(_message(), object)

        assert delivered == 1
        assert len(sink.messages) == 1
        worker._acknowledge.assert_awaited_once()

    asyncio.run(run())


def test_failed_delivery_is_scheduled_for_retry_without_acknowledging() -> None:
    async def run() -> None:
        worker = TransactionalOutboxWorker(AsyncMock(), _FailingSink())
        worker._record_failure = AsyncMock()
        worker._acknowledge = AsyncMock(return_value=True)

        delivered = await worker._deliver(_message(), object)

        assert delivered == 0
        worker._record_failure.assert_awaited_once()
        worker._acknowledge.assert_not_awaited()

    asyncio.run(run())


class _RecordingSession:
    """Capture a worker state update without requiring a database server."""

    def __init__(self) -> None:
        self.statement = None
        self.committed = False

    async def execute(self, statement):  # type: ignore[no-untyped-def]
        self.statement = statement
        return SimpleNamespace(rowcount=1)

    async def commit(self) -> None:
        self.committed = True


class _SessionContext:
    def __init__(self, session: _RecordingSession) -> None:
        self.session = session

    async def __aenter__(self) -> _RecordingSession:
        return self.session

    async def __aexit__(self, *_: object) -> None:
        return None


class _RecordingSessionFactory:
    def __init__(self, session: _RecordingSession) -> None:
        self.session = session

    def __call__(self) -> _SessionContext:
        return _SessionContext(self.session)


def _updated_values(statement) -> dict[str, object]:  # type: ignore[no-untyped-def]
    """Read SQLAlchemy update values while keeping the assertion DB-independent."""
    return {
        column.key: getattr(value, "value", value)
        for column, value in statement._values.items()  # noqa: SLF001 - test introspection
    }


def test_failure_schedules_deterministic_exponential_backoff() -> None:
    async def run() -> None:
        now = datetime(2026, 7, 25, tzinfo=UTC)
        session = _RecordingSession()
        worker = TransactionalOutboxWorker(
            _RecordingSessionFactory(session),  # type: ignore[arg-type]
            now=lambda: now,
            retry_initial_seconds=2,
            retry_max_seconds=60,
        )
        source = _message()
        message = OutboxMessage(
            context=source.context,
            event_id=source.event_id,
            event_key=source.event_key,
            event_type=source.event_type,
            payload=source.payload,
            occurred_at=source.occurred_at,
            attempts=3,
        )

        await worker._record_failure(
            message, IngestionOutboxEvent, RuntimeError("unavailable"), 0.25
        )

        assert session.committed is True
        values = _updated_values(session.statement)
        assert values["next_attempt_at"] == now + timedelta(seconds=8)
        assert values["last_error"] == "RuntimeError: unavailable"
        assert "dead_lettered_at" not in values

    asyncio.run(run())


def test_failure_dead_letters_at_the_configured_attempt_limit() -> None:
    async def run() -> None:
        now = datetime(2026, 7, 25, tzinfo=UTC)
        session = _RecordingSession()
        worker = TransactionalOutboxWorker(
            _RecordingSessionFactory(session),  # type: ignore[arg-type]
            now=lambda: now,
            max_attempts=2,
        )
        source = _message()
        message = OutboxMessage(
            context=source.context,
            event_id=source.event_id,
            event_key=source.event_key,
            event_type=source.event_type,
            payload=source.payload,
            occurred_at=source.occurred_at,
            attempts=2,
        )

        await worker._record_failure(
            message, IngestionOutboxEvent, RuntimeError("permanent"), 0.25
        )

        values = _updated_values(session.statement)
        assert values["dead_lettered_at"] == now
        assert "next_attempt_at" not in values

    asyncio.run(run())


def test_claim_query_uses_skip_locked_and_recovers_expired_leases() -> None:
    class _ClaimSession(_RecordingSession):
        async def scalars(self, statement):  # type: ignore[no-untyped-def]
            self.statement = statement
            return SimpleNamespace(all=lambda: [])

    async def run() -> None:
        session = _ClaimSession()
        worker = TransactionalOutboxWorker(
            _RecordingSessionFactory(session),  # type: ignore[arg-type]
            now=lambda: datetime(2026, 7, 25, tzinfo=UTC),
        )

        messages = await worker._claim(
            "fixture_ingestion", IngestionOutboxEvent, "occurred_at"
        )

        compiled = str(
            session.statement.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
        assert messages == []
        assert session.committed is True
        assert "FOR UPDATE SKIP LOCKED" in compiled
        assert "lease_expires_at IS NULL OR ingestion_outbox_events.lease_expires_at <=" in compiled
        assert "dead_lettered_at IS NULL" in compiled

    asyncio.run(run())


def test_lost_lease_cannot_mark_an_event_as_published() -> None:
    async def run() -> None:
        session = _RecordingSession()
        worker = TransactionalOutboxWorker(_RecordingSessionFactory(session))  # type: ignore[arg-type]

        async def lost_lease(statement):  # type: ignore[no-untyped-def]
            session.statement = statement
            return SimpleNamespace(rowcount=0)

        session.execute = lost_lease  # type: ignore[method-assign]
        acknowledged = await worker._acknowledge(_message(), IngestionOutboxEvent)

        assert acknowledged is False
        compiled = str(session.statement.compile(compile_kwargs={"literal_binds": True}))
        assert "ingestion_outbox_events.lease_owner" in compiled
        assert "ingestion_outbox_events.published_at IS NULL" in compiled

    asyncio.run(run())


def test_shutdown_drains_the_active_batch_before_the_worker_exits() -> None:
    async def run() -> None:
        worker = TransactionalOutboxWorker(AsyncMock(), shutdown_timeout_seconds=1)
        stop_event = asyncio.Event()
        started = asyncio.Event()
        release = asyncio.Event()
        completed = asyncio.Event()

        async def run_once() -> int:
            started.set()
            await release.wait()
            completed.set()
            return 0

        worker.run_once = run_once  # type: ignore[method-assign]
        task = asyncio.create_task(worker.run_forever(0.01, stop_event))
        await started.wait()
        stop_event.set()
        release.set()
        await task

        assert completed.is_set() is True

    asyncio.run(run())
