"""Explicit, bounded football-data.org Premier League fixture import orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.providers.football_data import FootballDataFixtureAdapter
from app.modules.ingestion.providers.football_data_client import FootballDataSeasonContext
from app.modules.ingestion.schemas import FixtureIngestionBatchResult
from app.modules.ingestion.service import FixtureIngestionService


class FootballDataFixtureSource(Protocol):
    """The two deliberately bounded reads required by one football-data.org import."""

    def discover_current_premier_league_season(self) -> FootballDataSeasonContext: ...

    def list_fixtures(self, season: FootballDataSeasonContext) -> list[dict[str, object]]: ...


@dataclass(frozen=True, slots=True)
class FootballDataImportResult:
    """Safe operational result that intentionally omits provider payloads and secrets."""

    season_start_year: int
    fixture_count: int
    ingestion: FixtureIngestionBatchResult


class FootballDataFixtureImportService:
    """Delegate a confirmed provider response to the existing canonical ingestion service."""

    def __init__(self, *, session: AsyncSession, source: FootballDataFixtureSource) -> None:
        self._session = session
        self._source = source

    async def import_current_premier_league_season(self) -> FootballDataImportResult:
        """Discover first, then import exactly one confirmed provider season page."""
        season = self._source.discover_current_premier_league_season()
        payloads = self._source.list_fixtures(season)
        ingestion = await FixtureIngestionService(
            session=self._session,
            provider_adapter=FootballDataFixtureAdapter(season),
        ).ingest(payloads)
        return FootballDataImportResult(
            season_start_year=season.season_start_year,
            fixture_count=len(payloads),
            ingestion=ingestion,
        )
