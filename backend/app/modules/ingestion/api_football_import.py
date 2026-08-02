"""Explicit, one-season API-Football fixture import orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.providers.api_football import ApiFootballFixtureAdapter
from app.modules.ingestion.providers.api_football_client import ApiFootballSeasonContext
from app.modules.ingestion.schemas import FixtureIngestionBatchResult
from app.modules.ingestion.service import FixtureIngestionService


class ApiFootballFixtureSource(Protocol):
    """The two deliberately bounded reads required by an API-Football import."""

    def discover_current_premier_league_season(self) -> ApiFootballSeasonContext: ...

    def list_fixtures(self, season: ApiFootballSeasonContext) -> list[dict[str, object]]: ...


@dataclass(frozen=True, slots=True)
class ApiFootballImportResult:
    """Safe operational result; it intentionally omits provider payloads and secrets."""

    season_year: int
    fixture_count: int
    ingestion: FixtureIngestionBatchResult


class ApiFootballFixtureImportService:
    """Use the existing canonical ingestion service without adding a scheduler or HTTP API."""

    def __init__(self, *, session: AsyncSession, source: ApiFootballFixtureSource) -> None:
        self._session = session
        self._source = source

    async def import_current_premier_league_season(self) -> ApiFootballImportResult:
        """Discover first, then import only that provider-confirmed season's fixture page."""
        season = self._source.discover_current_premier_league_season()
        payloads = self._source.list_fixtures(season)
        adapter = ApiFootballFixtureAdapter(season)
        ingestion = await FixtureIngestionService(
            session=self._session,
            provider_adapter=adapter,
        ).ingest(payloads)
        return ApiFootballImportResult(
            season_year=season.season_year,
            fixture_count=len(payloads),
            ingestion=ingestion,
        )
