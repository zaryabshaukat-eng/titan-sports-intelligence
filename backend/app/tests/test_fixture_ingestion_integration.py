"""Optional PostgreSQL integration coverage for the complete fixture-ingestion transaction."""

from __future__ import annotations

import asyncio
import os
from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.modules.ingestion.enums import IngestionAuditOutcome, RawPayloadStatus
from app.modules.ingestion.models import RawFixturePayload
from app.modules.ingestion.providers.fixture_feed_v1 import FixtureFeedV1Adapter
from app.modules.ingestion.service import FixtureIngestionService
from app.modules.sports.models import Fixture


def _payload_with_unique_provider_ids() -> dict[str, object]:
    """Create a valid fixture_feed_v1 payload that cannot clash with shared test database data."""
    suffix = uuid4().hex
    return {
        "fixture": {
            "id": f"fixture-{suffix}",
            "kickoff": "2026-08-01T15:00:00+00:00",
            "status": "SCHEDULED",
            "timezone": "Europe/London",
        },
        "sport": "football",
        "country": {
            "id": f"country-{suffix}",
            "name": "United Kingdom",
            "iso_code": "GB",
            "iso3_code": "GBR",
        },
        "league": {"id": f"league-{suffix}", "name": "English Football League"},
        "competition": {
            "id": f"competition-{suffix}",
            "name": "Premier League",
            "type": "league",
        },
        "season": {
            "id": f"season-{suffix}",
            "name": "2026/27",
            "start_date": "2026-08-01",
            "end_date": "2027-05-31",
            "status": "planned",
        },
        "teams": {
            "home": {"id": f"team-home-{suffix}", "name": f"Home FC {suffix}", "type": "club"},
            "away": {"id": f"team-away-{suffix}", "name": f"Away FC {suffix}", "type": "club"},
        },
    }


@pytest.mark.skipif(
    not os.getenv("TITAN_TEST_DATABASE_URL"),
    reason="TITAN_TEST_DATABASE_URL is not configured",
)
def test_fixture_ingestion_is_insert_update_and_retry_safe_against_postgresql() -> None:
    """Exercise the canonical upsert and immutable raw-payload path against migrated PostgreSQL."""
    database_url = os.environ["TITAN_TEST_DATABASE_URL"]

    async def run() -> None:
        engine = create_async_engine(database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with session_factory() as session:
                migrations_present = await session.scalar(
                    text(
                        "SELECT to_regclass('public.sports_fixture_statuses') IS NOT NULL "
                        "AND to_regclass('public.ingestion_raw_fixture_payloads') IS NOT NULL"
                    )
                )
                if not migrations_present:
                    pytest.skip("TITAN_TEST_DATABASE_URL has not been migrated")

                payload = _payload_with_unique_provider_ids()
                service = FixtureIngestionService(
                    session=session,
                    provider_adapter=FixtureFeedV1Adapter(),
                )
                inserted = await service.ingest([payload])
                replayed = await service.ingest([payload])

                updated_payload = deepcopy(payload)
                fixture_data = updated_payload["fixture"]
                assert isinstance(fixture_data, dict)
                fixture_data["status"] = "LIVE"
                updated = await service.ingest([updated_payload])
                await session.flush()

                assert inserted.items[0].outcome is IngestionAuditOutcome.INSERTED
                assert replayed.items[0].outcome is IngestionAuditOutcome.UNCHANGED
                assert updated.items[0].outcome is IngestionAuditOutcome.UPDATED
                assert inserted.items[0].fixture_id == updated.items[0].fixture_id

                fixture = await session.get(Fixture, inserted.items[0].fixture_id)
                assert fixture is not None
                raw_payloads = list(
                    (
                        await session.scalars(
                            select(RawFixturePayload).where(
                                RawFixturePayload.canonical_fixture_id == fixture.id
                            )
                        )
                    ).all()
                )
                assert len(raw_payloads) == 2
                assert {raw.validation_status for raw in raw_payloads} == {RawPayloadStatus.APPLIED}
                await session.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())
