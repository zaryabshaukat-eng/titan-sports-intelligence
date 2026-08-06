"""Contract tests for the bounded football-data.org fixture source and adapter."""

from __future__ import annotations

import json
from datetime import date
from io import BytesIO
from typing import Any
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request

import pytest

from app.core.config import Settings
from app.modules.ingestion.exceptions import PayloadValidationError
from app.modules.ingestion.providers.football_data import FootballDataFixtureAdapter
from app.modules.ingestion.providers.football_data_client import (
    FootballDataClient,
    FootballDataClientError,
    FootballDataSeasonContext,
)
from app.modules.ingestion.providers.football_data_country import (
    FootballDataCountryNormalizationError,
    normalize_football_data_country_code,
)


class _Response:
    def __init__(self, payload: dict[str, Any], *, status: int = 200) -> None:
        self._payload = payload
        self.status = status
        self.headers: dict[str, str] = {"x-requests-available-minute": "9"}

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode()


class _RecordingOpener:
    def __init__(self, payloads: list[dict[str, Any] | _Response]) -> None:
        self._payloads = iter(payloads)
        self.requests: list[Request] = []

    def __call__(self, request: Request, *, timeout: float) -> _Response:
        assert timeout == 10.0
        self.requests.append(request)
        payload = next(self._payloads)
        return payload if isinstance(payload, _Response) else _Response(payload)


def _competition_payload() -> dict[str, Any]:
    return {
        "id": 2021,
        "name": "Premier League",
        "code": "PL",
        "type": "LEAGUE",
        "area": {"id": 2072, "name": "England", "code": "ENG"},
        "currentSeason": {"id": 9001, "startDate": "2026-08-14", "endDate": "2027-05-23"},
    }


def _fixture_payload(*, status: str = "TIMED") -> dict[str, Any]:
    return {
        "id": 12345,
        "utcDate": "2026-08-14T19:00:00Z",
        "status": status,
        "area": {"id": 2072, "name": "England", "code": "ENG"},
        "competition": {"id": 2021, "name": "Premier League", "code": "PL", "type": "LEAGUE"},
        "season": {"id": 9001, "startDate": "2026-08-14", "endDate": "2027-05-23"},
        "homeTeam": {"id": 1, "name": "Home FC", "shortName": "Home"},
        "awayTeam": {"id": 2, "name": "Away FC", "shortName": "Away"},
        "matchday": 1,
        "stage": "REGULAR_SEASON",
    }


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


def test_runtime_token_configuration_uses_secretstr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TITAN_FOOTBALL_DATA_API_TOKEN", "token-not-for-output")
    settings = Settings(_env_file=None)

    assert settings.football_data_api_token is not None
    assert settings.football_data_api_token.get_secret_value() == "token-not-for-output"
    assert "token-not-for-output" not in str(settings.football_data_api_token)


def test_client_discovers_premier_league_and_uses_secret_header() -> None:
    opener = _RecordingOpener([_competition_payload()])
    client = FootballDataClient("test-token", opener=opener)

    season = client.discover_current_premier_league_season()

    assert season.competition_id == 2021
    assert season.season_start_year == 2026
    assert season.country_iso_code == "GB"
    request = opener.requests[0]
    assert urlparse(request.full_url).path.endswith("/competitions/PL")
    assert request.get_header("X-auth-token") == "test-token"


def test_client_reads_exactly_one_bounded_fixture_page() -> None:
    fixtures = [_fixture_payload()]
    opener = _RecordingOpener(
        [
            _competition_payload(),
            {"resultSet": {"count": 1}, "competition": {"id": 2021}, "matches": fixtures},
        ]
    )
    client = FootballDataClient("test-token", opener=opener)
    season = client.discover_current_premier_league_season()

    assert client.list_fixtures(season) == fixtures
    query = parse_qs(urlparse(opener.requests[1].full_url).query)
    assert query == {"season": ["2026"], "limit": ["500"]}


def test_client_stops_when_response_exceeds_bounded_page() -> None:
    opener = _RecordingOpener(
        [{"resultSet": {"count": 501}, "competition": {"id": 2021}, "matches": []}]
    )
    with pytest.raises(FootballDataClientError, match="exceeds the approved bounded page"):
        FootballDataClient("test-token", opener=opener).list_fixtures(_season_context())


def test_client_preserves_bounded_sanitized_http_error_without_token() -> None:
    token = "secret-token"

    def opener(request: Request, *, timeout: float) -> _Response:
        raise HTTPError(
            request.full_url,
            403,
            "forbidden",
            {"retry-after": "60", "authorization": token},
            BytesIO(json.dumps({"error": token + "x" * 600}).encode()),
        )

    with pytest.raises(FootballDataClientError) as exc_info:
        FootballDataClient(token, opener=opener).discover_current_premier_league_season()

    error = exc_info.value
    assert error.status_code == 403
    assert error.provider_error is not None and len(error.provider_error) <= 512
    assert token not in str(error)
    assert error.quota_headers == {"retry-after": "60"}


def test_explicit_country_normalization_fails_closed() -> None:
    assert normalize_football_data_country_code("ENG") == "GB"
    with pytest.raises(FootballDataCountryNormalizationError, match="unsupported"):
        normalize_football_data_country_code("GBR")


@pytest.mark.parametrize(
    ("provider_status", "canonical_status"),
    [
        ("SCHEDULED", "scheduled"),
        ("TIMED", "scheduled"),
        ("IN_PLAY", "live"),
        ("EXTRA_TIME", "live"),
        ("PENALTY_SHOOTOUT", "live"),
        ("PAUSED", "halftime"),
        ("FINISHED", "finished"),
        ("AWARDED", "finished"),
        ("SUSPENDED", "delayed"),
        ("POSTPONED", "postponed"),
        ("CANCELLED", "cancelled"),
    ],
)
def test_adapter_maps_approved_statuses(provider_status: str, canonical_status: str) -> None:
    normalized = FootballDataFixtureAdapter(_season_context()).normalize(
        _fixture_payload(status=provider_status)
    )

    assert normalized.fixture_status_code == canonical_status
    assert normalized.country.provider_id == "ENG"
    assert normalized.country.iso_code == "GB"
    assert normalized.home_team.country_iso_code is None
    assert normalized.timezone_iana_name == "UTC"
    assert normalized.scheduled_start_at.isoformat() == "2026-08-14T19:00:00+00:00"


def test_adapter_rejects_unknown_status_and_missing_required_fields() -> None:
    adapter = FootballDataFixtureAdapter(_season_context())
    with pytest.raises(
        PayloadValidationError, match="Fixture payload validation failed"
    ) as status_error:
        adapter.normalize(_fixture_payload(status="UNKNOWN"))
    assert "unsupported football-data.org fixture status" in status_error.value.errors[0]["message"]

    missing_fixture_id = _fixture_payload()
    del missing_fixture_id["id"]
    with pytest.raises(PayloadValidationError) as missing_error:
        adapter.normalize(missing_fixture_id)
    assert missing_error.value.errors[0]["path"] == "id"
