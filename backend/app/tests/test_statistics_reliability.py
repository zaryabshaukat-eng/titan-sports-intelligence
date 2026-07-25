"""Unit coverage for Statistics savepoint, retry, failure-evidence, and latest-query behavior."""

from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.modules.statistics.api import snapshots
from app.modules.statistics.enums import StatisticsAuditOutcome, StatisticsRunStatus
from app.modules.statistics.exceptions import StatisticsResolutionError
from app.modules.statistics.models import StatisticIngestionRun
from app.modules.statistics.providers.statistics_feed_v1 import StatisticsFeedV1Adapter
from app.modules.statistics.schemas import Pagination
from app.modules.statistics.service import StatisticsIngestionService


class _Savepoint(AbstractAsyncContextManager[None]):
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False


class _Session:
    def __init__(self, *, existing: object | None = None) -> None:
        self.existing = existing
        self.added: list[object] = []
        self.savepoint_count = 0

    async def scalar(self, statement: object) -> object | None:
        return self.existing

    async def flush(self) -> None:
        return None

    def add(self, entity: object) -> None:
        self.added.append(entity)

    def begin_nested(self) -> _Savepoint:
        self.savepoint_count += 1
        return _Savepoint()


def _payload() -> dict[str, object]:
    return {
        "fixture": {"provider": "fixture_feed_v1", "id": "fixture-1"},
        "observed_at": "2026-08-01T12:00:00+00:00",
        "statistics": [
            {
                "scope": "fixture",
                "category": {"code": "shots", "name": "Shots"},
                "values": {"total": 10},
            }
        ],
    }


def test_statistics_failure_uses_savepoint_and_retains_only_failure_evidence() -> None:
    async def run() -> None:
        session = _Session()
        service = StatisticsIngestionService(session, StatisticsFeedV1Adapter())
        service.repository.fixture = AsyncMock(return_value="fixture-id")
        service.repository.provider = AsyncMock(return_value=SimpleNamespace(id="provider-id"))
        service._append_snapshots = AsyncMock(side_effect=StatisticsResolutionError("bad team"))
        run = StatisticIngestionRun(
            provider_id="provider-id",
            status=StatisticsRunStatus.RUNNING,
            failed_count=0,
        )

        result = await service._one("provider-id", run, 0, _payload())

        assert session.savepoint_count == 1
        assert result.outcome == StatisticsAuditOutcome.VALIDATION_FAILED
        assert run.failed_count == 1
        assert not any(entity.__class__.__name__ == "StatisticSnapshot" for entity in session.added)
        assert {entity.__class__.__name__ for entity in session.added} >= {
            "RawStatisticPayload",
            "StatisticAudit",
            "StatisticsOutboxEvent",
        }

    asyncio.run(run())


def test_statistics_duplicate_payload_is_retry_safe_without_savepoint() -> None:
    async def run() -> None:
        existing = SimpleNamespace()
        session = _Session(existing=existing)
        service = StatisticsIngestionService(session, StatisticsFeedV1Adapter())
        run = StatisticIngestionRun(
            provider_id="provider-id",
            status=StatisticsRunStatus.RUNNING,
            failed_count=0,
        )

        result = await service._one("provider-id", run, 0, _payload())

        assert result.outcome == StatisticsAuditOutcome.UNCHANGED
        assert session.savepoint_count == 0
        assert session.added == []

    asyncio.run(run())


def test_latest_query_uses_row_number_per_statistic_series() -> None:
    class _ReadSession:
        statement: object | None = None

        async def scalar(self, statement: object) -> int:
            return 0

        async def scalars(self, statement: object) -> SimpleNamespace:
            self.statement = statement
            return SimpleNamespace(all=lambda: [])

    async def run() -> None:
        session = _ReadSession()
        result = await snapshots(None, None, Pagination(), session, latest_only=True)
        compiled = str(session.statement.compile(compile_kwargs={"literal_binds": True}))
        assert result.items == []
        assert "row_number() OVER" in compiled
        assert "PARTITION BY statistics_snapshots.series_id" in compiled

    asyncio.run(run())
