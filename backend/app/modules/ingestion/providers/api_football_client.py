"""Small, bounded API-Football client for explicit fixture imports only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
PREMIER_LEAGUE_ID = 39


class ApiFootballClientError(RuntimeError):
    """A safe provider failure that intentionally contains no credentials."""


@dataclass(frozen=True, slots=True)
class ApiFootballSeasonContext:
    """The provider-confirmed current Premier League season metadata."""

    league_id: int
    league_name: str
    country_name: str
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
        return ApiFootballSeasonContext(
            league_id=league_id,
            league_name=self._required_string(league, "name"),
            country_name=self._required_string(country, "name"),
            country_iso_code=self._required_iso2(country, "code"),
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
        except HTTPError as exc:
            raise ApiFootballClientError(f"API-Football returned HTTP {exc.code}") from exc
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
            raise ApiFootballClientError("API-Football returned a provider error")
        return decoded

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

    @classmethod
    def _required_iso2(cls, payload: dict[str, Any], key: str) -> str:
        value = cls._required_string(payload, key).upper()
        if len(value) != 2:
            raise ApiFootballClientError(f"API-Football response has an invalid '{key}'")
        return value

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
