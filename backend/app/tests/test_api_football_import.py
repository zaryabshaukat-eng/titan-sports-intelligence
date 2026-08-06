"""Unit tests proving the explicit source delegates persistence to existing ingestion."""

from __future__ import annotations

import asyncio
from datetime import date
from uuid import uuid4

import pytest

from app.modules.ingestion import api_football_import
from app.modules.ingestion.api_football_import import (
    ApiFootballFixtureImportService,
    ApiFootballImportResult,
)
from app.modules.ingestion.enums import IngestionAuditOutcome
from app.modules.ingestion.providers.api_football import ApiFootballFixtureAdapter
from app.modules.ingestion.providers.api_football_client import ApiFootballSeasonContext
from app.modules.ingestion.schemas import FixtureIngestionBatchResult, FixtureIngestionItemResult


class _Source:
    def __init__(self) -> None:
        self.discovered = False
        self.fixture_season: ApiFootballSeasonContext | None = None

    def discover_current_premier_league_season(self) -> ApiFootballSeasonContext:
        self.discovered = True
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

    def list_fixtures(self, season: ApiFootballSeasonContext) -> list[dict[str, object]]:
        self.fixture_season = season
        return [{"fixture": {"id": 123}}]


def test_import_delegates_confirmed_provider_payloads_to_existing_ingestion(
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
                provider_name="api_football",
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

    monkeypatch.setattr(api_football_import, "FixtureIngestionService", _RecordingIngestionService)
    source = _Source()

    async def run() -> ApiFootballImportResult:
        return await ApiFootballFixtureImportService(
            session=object(),  # type: ignore[arg-type]
            source=source,
        ).import_current_premier_league_season()

    result = asyncio.run(run())

    assert source.discovered is True
    assert source.fixture_season is not None
    assert result.season_year == 2026
    assert result.ingestion.inserted_count == 1
    assert captured["payloads"] == [{"fixture": {"id": 123}}]
    adapter = captured["adapter"]
    assert isinstance(adapter, ApiFootballFixtureAdapter)
    assert adapter.provider_name == "api_football"
