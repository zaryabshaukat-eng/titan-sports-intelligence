"""Optional PostgreSQL integration coverage for the complete fixture-ingestion transaction."""

from __future__ import annotations

import asyncio
import os
from copy import deepcopy
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.modules.ingestion.enums import IngestionAuditOutcome, ProviderEntityType, RawPayloadStatus
from app.modules.ingestion.models import ProviderEntityIdentity, RawFixturePayload
from app.modules.ingestion.providers.api_football import ApiFootballFixtureAdapter
from app.modules.ingestion.providers.api_football_client import ApiFootballSeasonContext
from app.modules.ingestion.providers.fixture_feed_v1 import FixtureFeedV1Adapter
from app.modules.ingestion.providers.football_data import FootballDataFixtureAdapter
from app.modules.ingestion.providers.football_data_client import FootballDataSeasonContext
from app.modules.ingestion.service import FixtureIngestionService
from app.modules.sports.models import Country, Fixture


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


def _api_football_payload_with_unique_fixture_id() -> dict[str, object]:
    """Return a provider-shaped API-Football payload for rolled-back integration coverage only."""
    fixture_id = int(uuid4().int % 1_000_000_000)
    return {
        "fixture": {
            "id": fixture_id,
            "timezone": "UTC",
            "date": "2026-08-14T19:00:00+00:00",
            "status": {"short": "NS"},
        },
        "league": {
            "id": 39,
            "name": "Premier League",
            "country": "England",
            "code": "GB-ENG",
            "season": 2026,
            "round": "Regular Season - 1",
        },
        "teams": {
            "home": {"id": fixture_id * 2, "name": f"Home {fixture_id}"},
            "away": {"id": fixture_id * 2 + 1, "name": f"Away {fixture_id}"},
        },
    }


def _api_football_season_context() -> ApiFootballSeasonContext:
    return ApiFootballSeasonContext(
        league_id=39,
        league_name="Premier League",
        country_name="England",
        country_provider_code="GB-ENG",
        country_iso_code="GB",
        season_year=2026,
        start_date=date(2026, 8, 14),
        end_date=date(2027, 5, 23),
    )


def _football_data_payload_with_unique_fixture_id() -> dict[str, object]:
    """Return a provider-shaped football-data.org payload for idempotency coverage only."""
    fixture_id = int(uuid4().int % 1_000_000_000)
    return {
        "id": fixture_id,
        "utcDate": "2026-08-14T19:00:00Z",
        "status": "TIMED",
        "area": {"id": 2072, "name": "England", "code": "ENG"},
        "competition": {"id": 2021, "name": "Premier League", "code": "PL", "type": "LEAGUE"},
        "season": {"id": 9001, "startDate": "2026-08-14", "endDate": "2027-05-23"},
        "homeTeam": {"id": fixture_id * 2, "name": f"Home {fixture_id}"},
        "awayTeam": {"id": fixture_id * 2 + 1, "name": f"Away {fixture_id}"},
        "matchday": 1,
    }


def _football_data_season_context() -> FootballDataSeasonContext:
    return FootballDataSeasonContext(
        competition_id=2021,
        competition_code="PL",
        competition_name="Premier League",
        country_name="England",
        country_provider_code="ENG",
        country_iso_code="GB",
        season_id=9001,
        season_start_year=2026,
        start_date=date(2026, 8, 14),
        end_date=date(2027, 5, 23),
    )


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


@pytest.mark.skipif(
    not os.getenv("TITAN_TEST_DATABASE_URL"),
    reason="TITAN_TEST_DATABASE_URL is not configured",
)
def test_api_football_country_normalization_uses_existing_idempotent_ingestion_path() -> None:
    """Verify GB-ENG provenance resolves to canonical GB without bypassing the resolver."""
    database_url = os.environ["TITAN_TEST_DATABASE_URL"]

    async def run() -> None:
        engine = create_async_engine(database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with session_factory() as session:
                payload = _api_football_payload_with_unique_fixture_id()
                service = FixtureIngestionService(
                    session=session,
                    provider_adapter=ApiFootballFixtureAdapter(_api_football_season_context()),
                )
                inserted = await service.ingest([payload])
                replayed = await service.ingest([payload])

                assert inserted.items[0].outcome is IngestionAuditOutcome.INSERTED
                assert replayed.items[0].outcome is IngestionAuditOutcome.UNCHANGED
                country_identity = await session.scalar(
                    select(ProviderEntityIdentity).where(
                        ProviderEntityIdentity.provider_name == "api_football",
                        ProviderEntityIdentity.entity_type == ProviderEntityType.COUNTRY,
                        ProviderEntityIdentity.provider_entity_id == "GB-ENG",
                    )
                )
                assert country_identity is not None
                country = await session.get(Country, country_identity.canonical_entity_id)
                assert country is not None
                assert country.iso_code == "GB"
                await session.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())


@pytest.mark.skipif(
    not os.getenv("TITAN_TEST_DATABASE_URL"),
    reason="TITAN_TEST_DATABASE_URL is not configured",
)
def test_football_data_country_normalization_uses_existing_idempotent_ingestion_path() -> None:
    """Verify ENG provenance resolves to canonical GB without bypassing the resolver."""
    database_url = os.environ["TITAN_TEST_DATABASE_URL"]

    async def run() -> None:
        engine = create_async_engine(database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with session_factory() as session:
                payload = _football_data_payload_with_unique_fixture_id()
                service = FixtureIngestionService(
                    session=session,
                    provider_adapter=FootballDataFixtureAdapter(_football_data_season_context()),
                )
                inserted = await service.ingest([payload])
                replayed = await service.ingest([payload])

                assert inserted.items[0].outcome is IngestionAuditOutcome.INSERTED
                assert replayed.items[0].outcome is IngestionAuditOutcome.UNCHANGED
                country_identity = await session.scalar(
                    select(ProviderEntityIdentity).where(
                        ProviderEntityIdentity.provider_name == "football_data",
                        ProviderEntityIdentity.entity_type == ProviderEntityType.COUNTRY,
                        ProviderEntityIdentity.provider_entity_id == "ENG",
                    )
                )
                assert country_identity is not None
                country = await session.get(Country, country_identity.canonical_entity_id)
                assert country is not None
                assert country.iso_code == "GB"
                await session.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())
