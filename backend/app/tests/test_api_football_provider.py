"""Contract tests for the bounded API-Football fixture source and adapter."""

from __future__ import annotations

import json
from datetime import date
from typing import Any
from urllib.parse import parse_qs, urlparse
from urllib.request import Request

import pytest

from app.modules.ingestion.exceptions import PayloadValidationError
from app.modules.ingestion.providers.api_football import ApiFootballFixtureAdapter
from app.modules.ingestion.providers.api_football_client import (
    PREMIER_LEAGUE_ID,
    ApiFootballClient,
    ApiFootballClientError,
    ApiFootballSeasonContext,
)


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode()


class _RecordingOpener:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self._payloads = iter(payloads)
        self.requests: list[Request] = []

    def __call__(self, request: Request, *, timeout: float) -> _Response:
        assert timeout == 10.0
        self.requests.append(request)
        return _Response(next(self._payloads))


def _coverage_payload() -> dict[str, Any]:
    return {
        "errors": {},
        "response": [
            {
                "league": {"id": 39, "name": "Premier League", "type": "League"},
                "country": {"name": "England", "code": "GB"},
                "seasons": [
                    {"year": 2025, "start": "2025-08-15", "end": "2026-05-24", "current": False},
                    {"year": 2026, "start": "2026-08-14", "end": "2027-05-23", "current": True},
                ],
            }
        ],
    }


def _fixture_payload() -> dict[str, Any]:
    return {
        "fixture": {
            "id": 10001,
            "timezone": "UTC",
            "date": "2026-08-14T19:00:00+00:00",
            "status": {"short": "NS"},
            "venue": {"id": 100, "name": "Titan Stadium", "city": "London"},
        },
        "league": {
            "id": 39,
            "name": "Premier League",
            "country": "England",
            "code": "GB",
            "season": 2026,
            "round": "Regular Season - 1",
        },
        "teams": {
            "home": {"id": 1, "name": "Titan Home"},
            "away": {"id": 2, "name": "Titan Away"},
        },
    }


def _season_context() -> ApiFootballSeasonContext:
    return ApiFootballSeasonContext(
        league_id=PREMIER_LEAGUE_ID,
        league_name="Premier League",
        country_name="England",
        country_iso_code="GB",
        season_year=2026,
        start_date=date(2026, 8, 14),
        end_date=date(2027, 5, 23),
    )


def test_client_discovers_current_season_then_requests_only_that_season() -> None:
    opener = _RecordingOpener(
        [
            _coverage_payload(),
            {"errors": {}, "paging": {"current": 1, "total": 1}, "response": [_fixture_payload()]},
        ]
    )
    client = ApiFootballClient("test-secret", opener=opener)

    season = client.discover_current_premier_league_season()
    fixtures = client.list_fixtures(season)

    assert season.season_year == 2026
    assert fixtures == [_fixture_payload()]
    coverage_query = parse_qs(urlparse(opener.requests[0].full_url).query)
    fixture_query = parse_qs(urlparse(opener.requests[1].full_url).query)
    assert coverage_query == {"id": ["39"]}
    assert fixture_query == {"league": ["39"], "season": ["2026"], "timezone": ["UTC"]}
    assert opener.requests[0].get_header("X-apisports-key") == "test-secret"


def test_client_rejects_unbounded_fixture_paging() -> None:
    opener = _RecordingOpener(
        [{"errors": {}, "paging": {"current": 1, "total": 2}, "response": []}]
    )
    client = ApiFootballClient("test-secret", opener=opener)

    with pytest.raises(ApiFootballClientError, match="single bounded page"):
        client.list_fixtures(_season_context())


def test_adapter_normalizes_api_football_fixture_with_confirmed_season() -> None:
    normalized = ApiFootballFixtureAdapter(_season_context()).normalize(_fixture_payload())

    assert normalized.provider_fixture_id == "10001"
    assert normalized.country.iso_code == "GB"
    assert normalized.competition.provider_id == "39"
    assert normalized.season.start_date == date(2026, 8, 14)
    assert normalized.home_team.name == "Titan Home"
    assert normalized.fixture_status_code == "scheduled"
    assert normalized.timezone_iana_name == "UTC"


def test_adapter_rejects_unrecognized_fixture_status() -> None:
    payload = _fixture_payload()
    payload["fixture"]["status"] = {"short": "WO"}  # type: ignore[index]

    with pytest.raises(PayloadValidationError) as exc_info:
        ApiFootballFixtureAdapter(_season_context()).normalize(payload)

    assert "unsupported API-Football fixture status" in exc_info.value.errors[0]["message"]
