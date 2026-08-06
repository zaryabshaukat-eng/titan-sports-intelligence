"""Tests proving football-data.org delegates persistence to existing fixture ingestion."""

from __future__ import annotations

import asyncio
from datetime import date
from uuid import uuid4

import pytest

from app.modules.ingestion import football_data_import
from app.modules.ingestion.enums import IngestionAuditOutcome
from app.modules.ingestion.football_data_import import FootballDataFixtureImportService
from app.modules.ingestion.providers.football_data import FootballDataFixtureAdapter
from app.modules.ingestion.providers.football_data_client import FootballDataSeasonContext
from app.modules.ingestion.schemas import FixtureIngestionBatchResult, FixtureIngestionItemResult


class _Source:
    def __init__(self) -> None:
        self.discovered = False
        self.fixture_season: FootballDataSeasonContext | None = None

    def discover_current_premier_league_season(self) -> FootballDataSeasonContext:
        self.discovered = True
        return _season_context()

    def list_fixtures(self, season: FootballDataSeasonContext) -> list[dict[str, object]]:
        self.fixture_season = season
        return [{"id": 12345}]


def _season_context() -> FootballDataSeasonContext:
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


def test_import_delegates_confirmed_payloads_to_existing_ingestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _RecordingIngestionService:
        def __init__(self, *, session: object, provider_adapter: object) -> None:
            captured["session"] = session
            captured["adapter"] = provider_adapter

        async def ingest(self, payloads: list[dict[str, object]]) -> FixtureIngestionBatchResult:
            captured["payloads"] = payloads
            return FixtureIngestionBatchResult(
                run_id=uuid4(),
                provider_name="football_data",
                received_count=1,
                inserted_count=1,
                updated_count=0,
                unchanged_count=0,
                failed_count=0,
                items=[
                    FixtureIngestionItemResult(
                        source_index=0,
                        outcome=IngestionAuditOutcome.INSERTED,
                        fixture_id=uuid4(),
                    )
                ],
            )

    monkeypatch.setattr(football_data_import, "FixtureIngestionService", _RecordingIngestionService)
    source = _Source()

    async def run() -> None:
        result = await FootballDataFixtureImportService(
            session=object(),  # type: ignore[arg-type]
            source=source,
        ).import_current_premier_league_season()
        assert result.season_start_year == 2026
        assert result.ingestion.inserted_count == 1

    asyncio.run(run())

    assert source.discovered is True
    assert source.fixture_season == _season_context()
    assert captured["payloads"] == [{"id": 12345}]
    assert isinstance(captured["adapter"], FootballDataFixtureAdapter)
