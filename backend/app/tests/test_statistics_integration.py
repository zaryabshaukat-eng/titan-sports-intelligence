"""Optional PostgreSQL integration tests for immutable Statistics ingestion and rollback."""

from __future__ import annotations

import asyncio
import os
from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.modules.ingestion.providers.fixture_feed_v1 import FixtureFeedV1Adapter
from app.modules.ingestion.service import FixtureIngestionService
from app.modules.statistics.enums import RawStatisticPayloadStatus, StatisticsAuditOutcome
from app.modules.statistics.models import RawStatisticPayload, StatisticSnapshot
from app.modules.statistics.providers.statistics_feed_v1 import StatisticsFeedV1Adapter
from app.modules.statistics.service import StatisticsIngestionService


def _fixture_payload(fixture_id: str, suffix: str) -> dict[str, object]:
    return {
        "fixture": {
            "id": fixture_id,
            "kickoff": "2026-08-01T15:00:00+00:00",
            "status": "SCHEDULED",
            "timezone": "Europe/London",
        },
        "sport": "football",
        "country": {"id": f"country-{suffix}", "name": "United Kingdom", "iso_code": "GB"},
        "league": {"id": f"league-{suffix}", "name": "English Football League"},
        "competition": {"id": f"competition-{suffix}", "name": "Premier League", "type": "league"},
        "season": {
            "id": f"season-{suffix}",
            "name": "2026/27",
            "start_date": "2026-08-01",
            "end_date": "2027-05-31",
            "status": "planned",
        },
        "teams": {
            "home": {"id": f"home-{suffix}", "name": f"Home FC {suffix}", "type": "club"},
            "away": {"id": f"away-{suffix}", "name": f"Away FC {suffix}", "type": "club"},
        },
    }


def _statistics_payload(fixture_id: str) -> dict[str, object]:
    return {
        "fixture": {"provider": "fixture_feed_v1", "id": fixture_id},
        "observed_at": "2026-08-01T12:00:00+00:00",
        "statistics": [
            {
                "scope": "fixture",
                "category": {"code": "shots", "name": "Shots"},
                "values": {"total": 10},
            }
        ],
    }


@pytest.mark.skipif(
    not os.getenv("TITAN_TEST_DATABASE_URL"), reason="TITAN_TEST_DATABASE_URL is not configured"
)
def test_statistics_ingestion_is_immutable_retry_safe_and_rolls_back_partial_payloads() -> None:
    async def run() -> None:
        engine = create_async_engine(os.environ["TITAN_TEST_DATABASE_URL"], pool_pre_ping=True)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with factory() as session:
                migrated = await session.scalar(
                    text("SELECT to_regclass('public.statistics_snapshots') IS NOT NULL")
                )
                if not migrated:
                    pytest.skip("TITAN_TEST_DATABASE_URL has not been migrated through Statistics")
                suffix = uuid4().hex
                fixture_id = f"statistics-fixture-{suffix}"
                fixture = await FixtureIngestionService(
                    session=session, provider_adapter=FixtureFeedV1Adapter()
                ).ingest([_fixture_payload(fixture_id, suffix)])
                assert fixture.inserted_count == 1
                service = StatisticsIngestionService(session, StatisticsFeedV1Adapter())
                payload = _statistics_payload(fixture_id)
                inserted = await service.ingest([payload])
                replay = await service.ingest([payload])
                invalid = deepcopy(payload)
                invalid["observed_at"] = "2026-08-01T12:05:00+00:00"
                stats = invalid["statistics"]
                assert isinstance(stats, list)
                stats.append(
                    {
                        "scope": "team",
                        "category": {"code": "possession", "name": "Possession"},
                        "team": {"id": "unknown", "name": "Unknown Team"},
                        "values": {"percentage": 50},
                    }
                )
                failed = await service.ingest([invalid])
                await session.flush()

                assert inserted.items[0].outcome == StatisticsAuditOutcome.PROCESSED
                assert replay.items[0].outcome == StatisticsAuditOutcome.UNCHANGED
                assert failed.items[0].outcome == StatisticsAuditOutcome.VALIDATION_FAILED
                assert (
                    await session.scalar(select(func.count()).select_from(StatisticSnapshot)) == 1
                )
                raw = list((await session.scalars(select(RawStatisticPayload))).all())
                assert any(
                    item.validation_status is RawStatisticPayloadStatus.INVALID for item in raw
                )
                await session.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())
