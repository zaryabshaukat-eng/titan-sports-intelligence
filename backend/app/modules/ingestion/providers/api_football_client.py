"""Small, bounded API-Football client for explicit fixture imports only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.modules.ingestion.providers.api_football_country import (
    ApiFootballCountryNormalizationError,
    normalize_api_football_country_code,
)

API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
PREMIER_LEAGUE_ID = 39
_MAX_PROVIDER_ERROR_LENGTH = 512
_MAX_PROVIDER_ERROR_ITEMS = 8
_SAFE_QUOTA_HEADER_NAMES = {
    "retry-after",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "x-rate-limit-limit",
    "x-rate-limit-remaining",
    "x-rate-limit-reset",
}


class ApiFootballClientError(RuntimeError):
    """A safe provider failure that intentionally contains no credentials."""

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
            quota_details = ", ".join(
                f"{name}={value}" for name, value in self.quota_headers.items()
            )
            details.append("quota " + quota_details)
        suffix = f" ({'; '.join(details)})" if details else ""
        super().__init__(f"{message}{suffix}")


@dataclass(frozen=True, slots=True)
class ApiFootballSeasonContext:
    """The provider-confirmed current Premier League season metadata."""

    league_id: int
    league_name: str
    country_name: str
    country_provider_code: str
    country_iso_code: str
    season_year: int
    start_date: date
    end_date: date


class UrlOpener(Protocol):
    """Minimal seam for deterministic client tests without a network request."""

    def __call__(self, request: Request, *, timeout: float) -> Any: ...


class ApiFootballClient:
    """Make only the two requests needed for one bounded Premier League import."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 10.0,
        opener: UrlOpener = urlopen,
    ) -> None:
        if not api_key.strip():
            raise ValueError("API-Football API key must not be empty")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._opener = opener

    def discover_current_premier_league_season(self) -> ApiFootballSeasonContext:
        """Discover the provider-designated current season; never infer its value locally."""
        payload = self._get_json("/leagues", {"id": PREMIER_LEAGUE_ID})
        response = self._single_response_item(payload, "/leagues?id=39")

        league = self._required_object(response, "league")
        country = self._required_object(response, "country")
        league_id = self._required_int(league, "id")
        if league_id != PREMIER_LEAGUE_ID:
            raise ApiFootballClientError("API-Football returned an unexpected competition identity")
        if str(league.get("type", "")).lower() != "league":
            raise ApiFootballClientError("API-Football target is not a league competition")

        seasons = response.get("seasons")
        if not isinstance(seasons, list):
            raise ApiFootballClientError("API-Football league response did not include seasons")
        current = [
            season
            for season in seasons
            if isinstance(season, dict) and season.get("current") is True
        ]
        if len(current) != 1:
            raise ApiFootballClientError(
                "API-Football did not identify exactly one current Premier League season"
            )
        season = current[0]
        country_provider_code = self._required_string(country, "code")
        try:
            country_iso_code = normalize_api_football_country_code(country_provider_code)
        except ApiFootballCountryNormalizationError as exc:
            raise ApiFootballClientError(str(exc)) from exc
        return ApiFootballSeasonContext(
            league_id=league_id,
            league_name=self._required_string(league, "name"),
            country_name=self._required_string(country, "name"),
            country_provider_code=country_provider_code,
            country_iso_code=country_iso_code,
            season_year=self._required_int(season, "year"),
            start_date=self._required_date(season, "start"),
            end_date=self._required_date(season, "end"),
        )

    def list_fixtures(self, season: ApiFootballSeasonContext) -> list[dict[str, Any]]:
        """Fetch one confirmed season without pagination or any adjacent provider domains."""
        if season.league_id != PREMIER_LEAGUE_ID:
            raise ValueError("only the approved Premier League competition may be imported")
        payload = self._get_json(
            "/fixtures",
            {"league": season.league_id, "season": season.season_year, "timezone": "UTC"},
        )
        paging = payload.get("paging")
        if not isinstance(paging, dict) or paging.get("total") != 1:
            raise ApiFootballClientError(
                "API-Football fixture response is not a single bounded page; import stopped"
            )
        response = payload.get("response")
        if not isinstance(response, list) or not all(isinstance(item, dict) for item in response):
            raise ApiFootballClientError("API-Football fixture response was not a list of objects")
        return response

    def _get_json(self, path: str, query: dict[str, int | str]) -> dict[str, Any]:
        request = Request(
            f"{API_FOOTBALL_BASE_URL}{path}?{urlencode(query)}",
            headers={"x-apisports-key": self._api_key, "Accept": "application/json"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                raw_body = response.read()
                status_code = self._response_status(response)
                quota_headers = self._safe_quota_headers(getattr(response, "headers", None))
        except HTTPError as exc:
            try:
                error_body = exc.read()
            except OSError:
                error_body = b""
            raise ApiFootballClientError(
                "API-Football returned an HTTP error",
                status_code=exc.code,
                provider_error=self._provider_error_from_body(error_body),
                quota_headers=self._safe_quota_headers(exc.headers),
            ) from exc
        except URLError as exc:
            raise ApiFootballClientError("API-Football network request failed") from exc
        except TimeoutError as exc:
            raise ApiFootballClientError("API-Football request timed out") from exc

        try:
            decoded = json.loads(raw_body)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiFootballClientError("API-Football returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise ApiFootballClientError("API-Football returned an invalid response envelope")
        errors = decoded.get("errors")
        if errors not in (None, {}, []):
            raise ApiFootballClientError(
                "API-Football returned a provider error",
                status_code=status_code,
                provider_error=self._safe_provider_error_summary(errors),
                quota_headers=quota_headers,
            )
        return decoded

    def _provider_error_from_body(self, body: bytes) -> str | None:
        """Extract only a bounded provider error field from an HTTP-error JSON envelope."""
        try:
            decoded = json.loads(body)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(decoded, dict):
            return None
        errors = decoded.get("errors")
        return self._safe_provider_error_summary(errors)

    def _safe_provider_error_summary(self, errors: Any) -> str:
        """Create a bounded, credential-redacted summary without retaining the raw response."""
        items: list[str] = []
        if isinstance(errors, dict):
            for key, value in list(errors.items())[:_MAX_PROVIDER_ERROR_ITEMS]:
                items.append(f"{self._safe_text(key)}: {self._safe_error_value(value)}")
        elif isinstance(errors, list):
            items = [self._safe_error_value(item) for item in errors[:_MAX_PROVIDER_ERROR_ITEMS]]
        else:
            items = [self._safe_error_value(errors)]
        return self._bound_text("; ".join(items))

    def _safe_error_value(self, value: Any) -> str:
        if isinstance(value, str):
            return self._safe_text(value)
        if isinstance(value, (int, float, bool)) or value is None:
            return self._safe_text(str(value))
        if isinstance(value, list):
            return ", ".join(
                self._safe_error_value(item) for item in value[:_MAX_PROVIDER_ERROR_ITEMS]
            )
        return "[structured provider error]"

    def _safe_text(self, value: object) -> str:
        return self._bound_text(str(value).replace(self._api_key, "[REDACTED]"))

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
    def _bound_text(value: str) -> str:
        if len(value) <= _MAX_PROVIDER_ERROR_LENGTH:
            return value
        return f"{value[:_MAX_PROVIDER_ERROR_LENGTH]}…"

    @staticmethod
    def _single_response_item(payload: dict[str, Any], context: str) -> dict[str, Any]:
        response = payload.get("response")
        if (
            not isinstance(response, list)
            or len(response) != 1
            or not isinstance(response[0], dict)
        ):
            raise ApiFootballClientError(
                f"API-Football returned an unexpected response for {context}"
            )
        return response[0]

    @staticmethod
    def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
        value = payload.get(key)
        if not isinstance(value, dict):
            raise ApiFootballClientError(f"API-Football response is missing '{key}'")
        return value

    @staticmethod
    def _required_string(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ApiFootballClientError(f"API-Football response has an invalid '{key}'")
        return value.strip()

    @staticmethod
    def _required_int(payload: dict[str, Any], key: str) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ApiFootballClientError(f"API-Football response has an invalid '{key}'")
        return value

    @staticmethod
    def _required_date(payload: dict[str, Any], key: str) -> date:
        value = payload.get(key)
        if not isinstance(value, str):
            raise ApiFootballClientError(f"API-Football response has an invalid '{key}'")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ApiFootballClientError(f"API-Football response has an invalid '{key}'") from exc
