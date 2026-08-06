"""Bounded football-data.org client for explicit Premier League fixture imports only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.modules.ingestion.providers.football_data_country import (
    FootballDataCountryNormalizationError,
    normalize_football_data_country_code,
)

FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
PREMIER_LEAGUE_CODE = "PL"
PREMIER_LEAGUE_ID = 2021
_MAX_PROVIDER_ERROR_LENGTH = 512
_SAFE_QUOTA_HEADER_NAMES = {"retry-after", "x-requests-available-minute"}


class FootballDataClientError(RuntimeError):
    """Safe provider failure that intentionally contains no credential or request headers."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        provider_error: str | None = None,
        quota_headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.provider_error = provider_error
        self.quota_headers = quota_headers or {}
        details: list[str] = []
        if status_code is not None:
            details.append(f"HTTP {status_code}")
        if provider_error:
            details.append(provider_error)
        if self.quota_headers:
            details.append(
                "quota " + ", ".join(f"{key}={value}" for key, value in self.quota_headers.items())
            )
        suffix = f" ({'; '.join(details)})" if details else ""
        super().__init__(f"{message}{suffix}")


@dataclass(frozen=True, slots=True)
class FootballDataSeasonContext:
    """Provider-confirmed Premier League and current-season metadata."""

    competition_id: int
    competition_code: str
    competition_name: str
    country_name: str
    country_provider_code: str
    country_iso_code: str
    season_id: int
    season_start_year: int
    start_date: date
    end_date: date


class UrlOpener(Protocol):
    """Minimal seam for deterministic client tests without network access."""

    def __call__(self, request: Request, *, timeout: float) -> Any: ...


class FootballDataClient:
    """Make exactly two bounded reads for one explicit Premier League import."""

    def __init__(
        self,
        api_token: str,
        *,
        timeout_seconds: float = 10.0,
        opener: UrlOpener = urlopen,
    ) -> None:
        if not api_token.strip():
            raise ValueError("football-data.org API token must not be empty")
        self._api_token = api_token
        self._timeout_seconds = timeout_seconds
        self._opener = opener

    def discover_current_premier_league_season(self) -> FootballDataSeasonContext:
        """Discover the provider-designated current season; never infer it locally."""
        payload = self._get_json(f"/competitions/{PREMIER_LEAGUE_CODE}", {})
        competition_id = self._required_int(payload, "id")
        competition_code = self._required_string(payload, "code")
        if competition_id != PREMIER_LEAGUE_ID or competition_code != PREMIER_LEAGUE_CODE:
            raise FootballDataClientError(
                "football-data.org returned an unexpected competition identity"
            )
        if self._required_string(payload, "type") != "LEAGUE":
            raise FootballDataClientError("football-data.org target is not a league competition")
        area = self._required_object(payload, "area")
        season = self._required_object(payload, "currentSeason")
        start_date = self._required_date(season, "startDate")
        end_date = self._required_date(season, "endDate")
        country_provider_code = self._required_string(area, "code")
        try:
            country_iso_code = normalize_football_data_country_code(country_provider_code)
        except FootballDataCountryNormalizationError as exc:
            raise FootballDataClientError(str(exc)) from exc
        return FootballDataSeasonContext(
            competition_id=competition_id,
            competition_code=competition_code,
            competition_name=self._required_string(payload, "name"),
            country_name=self._required_string(area, "name"),
            country_provider_code=country_provider_code,
            country_iso_code=country_iso_code,
            season_id=self._required_int(season, "id"),
            season_start_year=start_date.year,
            start_date=start_date,
            end_date=end_date,
        )

    def list_fixtures(self, season: FootballDataSeasonContext) -> list[dict[str, Any]]:
        """Read one season page and stop rather than paginate beyond the approved scope."""
        if (
            season.competition_id != PREMIER_LEAGUE_ID
            or season.competition_code != PREMIER_LEAGUE_CODE
        ):
            raise ValueError("only the approved Premier League competition may be imported")
        payload = self._get_json(
            f"/competitions/{PREMIER_LEAGUE_CODE}/matches",
            {"season": season.season_start_year, "limit": 500},
        )
        result_set = self._required_object(payload, "resultSet")
        count = self._required_int(result_set, "count")
        if count > 500:
            raise FootballDataClientError(
                "football-data.org fixture response exceeds the approved bounded page"
            )
        competition = self._required_object(payload, "competition")
        if self._required_int(competition, "id") != season.competition_id:
            raise FootballDataClientError(
                "football-data.org fixture response has an unexpected competition"
            )
        matches = payload.get("matches")
        if not isinstance(matches, list) or not all(isinstance(item, dict) for item in matches):
            raise FootballDataClientError(
                "football-data.org fixture response was not a list of objects"
            )
        if len(matches) != count:
            raise FootballDataClientError(
                "football-data.org fixture response count did not match its payload"
            )
        return matches

    def _get_json(self, path: str, query: dict[str, int | str]) -> dict[str, Any]:
        suffix = f"?{urlencode(query)}" if query else ""
        request = Request(
            f"{FOOTBALL_DATA_BASE_URL}{path}{suffix}",
            headers={"X-Auth-Token": self._api_token, "Accept": "application/json"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                body = response.read()
                status_code = self._response_status(response)
                quota_headers = self._safe_quota_headers(getattr(response, "headers", None))
        except HTTPError as exc:
            try:
                body = exc.read()
            except OSError:
                body = b""
            raise FootballDataClientError(
                "football-data.org returned an HTTP error",
                status_code=exc.code,
                provider_error=self._provider_error_from_body(body),
                quota_headers=self._safe_quota_headers(exc.headers),
            ) from exc
        except URLError as exc:
            raise FootballDataClientError("football-data.org network request failed") from exc
        except TimeoutError as exc:
            raise FootballDataClientError("football-data.org request timed out") from exc
        try:
            decoded = json.loads(body)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FootballDataClientError("football-data.org returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise FootballDataClientError("football-data.org returned an invalid response envelope")
        if status_code is not None and not 200 <= status_code < 300:
            raise FootballDataClientError(
                "football-data.org returned an HTTP error",
                status_code=status_code,
                provider_error=self._provider_error_from_payload(decoded),
                quota_headers=quota_headers,
            )
        return decoded

    def _provider_error_from_body(self, body: bytes) -> str | None:
        try:
            decoded = json.loads(body)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return self._provider_error_from_payload(decoded)

    def _provider_error_from_payload(self, payload: object) -> str | None:
        if not isinstance(payload, dict):
            return None
        error = payload.get("error")
        if isinstance(error, str) and error.strip():
            return self._safe_text(error)
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return self._safe_text(message)
        return None

    def _safe_text(self, value: str) -> str:
        sanitized = value.replace(self._api_token, "[REDACTED]")
        return (
            sanitized
            if len(sanitized) <= _MAX_PROVIDER_ERROR_LENGTH
            else f"{sanitized[: _MAX_PROVIDER_ERROR_LENGTH - 1]}…"
        )

    @staticmethod
    def _response_status(response: Any) -> int | None:
        status = getattr(response, "status", None)
        if isinstance(status, int):
            return status
        getcode = getattr(response, "getcode", None)
        code = getcode() if callable(getcode) else None
        return code if isinstance(code, int) else None

    @staticmethod
    def _safe_quota_headers(headers: Any) -> dict[str, str]:
        if headers is None:
            return {}
        return {
            name.lower(): str(value)[:128]
            for name, value in headers.items()
            if name.lower() in _SAFE_QUOTA_HEADER_NAMES
        }

    @staticmethod
    def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
        value = payload.get(key)
        if not isinstance(value, dict):
            raise FootballDataClientError(f"football-data.org response is missing '{key}'")
        return value

    @staticmethod
    def _required_string(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise FootballDataClientError(f"football-data.org response has an invalid '{key}'")
        return value.strip()

    @staticmethod
    def _required_int(payload: dict[str, Any], key: str) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise FootballDataClientError(f"football-data.org response has an invalid '{key}'")
        return value

    @staticmethod
    def _required_date(payload: dict[str, Any], key: str) -> date:
        value = payload.get(key)
        if not isinstance(value, str):
            raise FootballDataClientError(f"football-data.org response has an invalid '{key}'")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise FootballDataClientError(
                f"football-data.org response has an invalid '{key}'"
            ) from exc
