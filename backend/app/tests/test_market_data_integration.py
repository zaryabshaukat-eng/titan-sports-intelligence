"""Optional PostgreSQL integration coverage for fixture-linked immutable odds ingestion."""

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
from app.modules.market_data.enums import OddsAuditOutcome, OddsMovementType, RawOddsPayloadStatus
from app.modules.market_data.models import OddsMovement, OddsSnapshot, RawOddsPayload
from app.modules.market_data.providers.odds_feed_v1 import OddsFeedV1Adapter
from app.modules.market_data.service import OddsIngestionService


def _fixture_payload(fixture_id: str, suffix: str) -> dict[str, object]:
    """Create a unique valid Fixture Ingestion payload to establish the canonical dependency."""
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


def _odds_payload(fixture_id: str) -> dict[str, object]:
    """Create a complete, authoritative 1X2 source market for lifecycle movement testing."""
    return {
        "fixture": {"provider": "fixture_feed_v1", "id": fixture_id},
        "bookmaker": {"id": "bookmaker-titan", "name": "TITAN Sportsbook", "code": "titan"},
        "observed_at": "2026-08-01T12:00:00+00:00",
        "markets": [
            {
                "id": "market-1x2",
                "market_type": {"code": "match_winner", "name": "Match Winner"},
                "status": "open",
                "selections_complete": True,
                "selections": [
                    {"id": "home", "key": "home", "name": "Home", "decimal_odds": "1.80"},
                    {"id": "draw", "key": "draw", "name": "Draw", "decimal_odds": "3.50"},
                    {"id": "away", "key": "away", "name": "Away", "decimal_odds": "4.20"},
                ],
            }
        ],
    }


@pytest.mark.skipif(
    not os.getenv("TITAN_TEST_DATABASE_URL"),
    reason="TITAN_TEST_DATABASE_URL is not configured",
)
def test_market_data_is_fixture_linked_immutable_and_retry_safe_against_postgresql() -> None:
    """Exercise the canonical fixture-to-odds pipeline in one rollback-only transaction."""
    database_url = os.environ["TITAN_TEST_DATABASE_URL"]

    async def run() -> None:
        engine = create_async_engine(database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with session_factory() as session:
                migrations_present = await session.scalar(
                    text(
                        "SELECT to_regclass("
                        "'public.ingestion_fixture_provider_identities') IS NOT NULL "
                        "AND to_regclass('public.market_data_odds_snapshots') IS NOT NULL"
                    )
                )
                if not migrations_present:
                    pytest.skip("TITAN_TEST_DATABASE_URL has not been migrated to Phase 2.3.3")

                suffix = uuid4().hex
                fixture_id = f"fixture-{suffix}"
                fixture_result = await FixtureIngestionService(
                    session=session,
                    provider_adapter=FixtureFeedV1Adapter(),
                ).ingest([_fixture_payload(fixture_id, suffix)])
                assert fixture_result.inserted_count == 1

                service = OddsIngestionService(
                    session=session,
                    provider_adapter=OddsFeedV1Adapter(),
                )
                opening_payload = _odds_payload(fixture_id)
                opening = await service.ingest([opening_payload])
                replay = await service.ingest([opening_payload])

                price_update = deepcopy(opening_payload)
                price_update["observed_at"] = "2026-08-01T12:05:00+00:00"
                markets = price_update["markets"]
                assert isinstance(markets, list) and isinstance(markets[0], dict)
                selections = markets[0]["selections"]
                assert isinstance(selections, list) and isinstance(selections[0], dict)
                selections[0]["decimal_odds"] = "1.90"
                changed = await service.ingest([price_update])

                suspended_payload = deepcopy(price_update)
                suspended_payload["observed_at"] = "2026-08-01T12:10:00+00:00"
                suspended_markets = suspended_payload["markets"]
                assert isinstance(suspended_markets, list) and isinstance(
                    suspended_markets[0], dict
                )
                suspended_markets[0]["status"] = "suspended"
                suspended = await service.ingest([suspended_payload])

                closing_payload = deepcopy(suspended_payload)
                closing_payload["observed_at"] = "2026-08-01T12:15:00+00:00"
                closing_markets = closing_payload["markets"]
                assert isinstance(closing_markets, list) and isinstance(closing_markets[0], dict)
                closing_markets[0]["status"] = "closed"
                closed = await service.ingest([closing_payload])
                await session.flush()

                assert opening.items[0].outcome is OddsAuditOutcome.PROCESSED
                assert opening.items[0].snapshots_created == 3
                assert replay.items[0].outcome is OddsAuditOutcome.UNCHANGED
                assert changed.items[0].snapshots_created == 1
                assert changed.items[0].snapshots_ignored == 2
                assert suspended.items[0].movements_detected >= 1
                assert closed.items[0].movements_detected >= 3

                snapshots = await session.scalar(select(func.count()).select_from(OddsSnapshot))
                raw_payloads = list((await session.scalars(select(RawOddsPayload))).all())
                movements = list((await session.scalars(select(OddsMovement))).all())
                assert snapshots == 4
                assert len(raw_payloads) == 4
                assert {payload.validation_status for payload in raw_payloads} == {
                    RawOddsPayloadStatus.APPLIED
                }
                assert OddsMovementType.PRICE_INCREASED in {
                    movement.movement_type for movement in movements
                }
                assert OddsMovementType.MARKET_SUSPENDED in {
                    movement.movement_type for movement in movements
                }
                assert (
                    sum(
                        movement.movement_type is OddsMovementType.CLOSING for movement in movements
                    )
                    == 3
                )
                await session.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())
