"""API-Football fixture payload adapter for the provider-neutral ingestion pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.ingestion.exceptions import PayloadValidationError
from app.modules.ingestion.providers.api_football_client import ApiFootballSeasonContext
from app.modules.ingestion.providers.base import FixtureProviderAdapter
from app.modules.ingestion.schemas import (
    NormalizedCompetition,
    NormalizedCountry,
    NormalizedFixture,
    NormalizedLeague,
    NormalizedSeason,
    NormalizedTeam,
    NormalizedVenue,
)
from app.modules.sports.enums import CompetitionType, SeasonStatus, TeamType


class _ApiFootballFixtureStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    short: str = Field(min_length=1, max_length=16)


class _ApiFootballVenue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    name: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=128)


class _ApiFootballFixture(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    timezone: str = Field(min_length=3, max_length=64)
    date: datetime
    status: _ApiFootballFixtureStatus
    venue: _ApiFootballVenue | None = None


class _ApiFootballLeague(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = Field(min_length=1, max_length=160)
    country: str = Field(min_length=1, max_length=160)
    code: str = Field(min_length=2, max_length=2)
    season: int
    round: str | None = Field(default=None, max_length=128)


class _ApiFootballTeam(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = Field(min_length=1, max_length=160)


class _ApiFootballTeams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    home: _ApiFootballTeam
    away: _ApiFootballTeam


class _ApiFootballFixturePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fixture: _ApiFootballFixture
    league: _ApiFootballLeague
    teams: _ApiFootballTeams


_STATUS_MAP: dict[str, str] = {
    "TBD": "scheduled",
    "NS": "scheduled",
    "1H": "live",
    "HT": "halftime",
    "2H": "live",
    "ET": "live",
    "BT": "live",
    "P": "live",
    "LIVE": "live",
    "FT": "finished",
    "AET": "finished",
    "PEN": "finished",
    "PST": "postponed",
    "CANC": "cancelled",
    "ABD": "abandoned",
    "SUSP": "delayed",
    "INT": "delayed",
}


def _validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
    return [
        {
            "path": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors(include_input=False)
    ]


class ApiFootballFixtureAdapter(FixtureProviderAdapter):
    """Normalize authentic API-Football fixture response items using confirmed season context."""

    provider_name = "api_football"

    def __init__(self, season: ApiFootballSeasonContext) -> None:
        self._season = season

    def extract_fixture_id(self, payload: dict[str, Any]) -> str | None:
        fixture = payload.get("fixture")
        if not isinstance(fixture, dict) or not isinstance(fixture.get("id"), int):
            return None
        return str(fixture["id"])

    def normalize(self, payload: dict[str, Any]) -> NormalizedFixture:
        try:
            source = _ApiFootballFixturePayload.model_validate(payload)
            if source.league.id != self._season.league_id:
                raise ValueError("fixture league does not match the confirmed import competition")
            if source.league.season != self._season.season_year:
                raise ValueError("fixture season does not match the confirmed import season")
            if source.league.code.upper() != self._season.country_iso_code:
                raise ValueError("fixture country does not match the confirmed import country")
            status = _STATUS_MAP.get(source.fixture.status.short.upper())
            if status is None:
                raise ValueError(
                    f"unsupported API-Football fixture status '{source.fixture.status.short}'"
                )
            venue = self._normalized_venue(source.fixture.venue)
            return NormalizedFixture(
                provider_fixture_id=str(source.fixture.id),
                sport="football",
                country=NormalizedCountry(
                    provider_id=source.league.code.upper(),
                    name=source.league.country,
                    iso_code=source.league.code,
                ),
                league=NormalizedLeague(
                    provider_id=str(source.league.id),
                    name=source.league.name,
                ),
                competition=NormalizedCompetition(
                    provider_id=str(source.league.id),
                    name=source.league.name,
                    competition_type=CompetitionType.LEAGUE,
                ),
                season=NormalizedSeason(
                    provider_id=str(self._season.season_year),
                    name=str(self._season.season_year),
                    start_date=self._season.start_date,
                    end_date=self._season.end_date,
                    status=SeasonStatus.ACTIVE,
                ),
                home_team=NormalizedTeam(
                    provider_id=str(source.teams.home.id),
                    name=source.teams.home.name,
                    team_type=TeamType.CLUB,
                    country_iso_code=source.league.code,
                ),
                away_team=NormalizedTeam(
                    provider_id=str(source.teams.away.id),
                    name=source.teams.away.name,
                    team_type=TeamType.CLUB,
                    country_iso_code=source.league.code,
                ),
                fixture_status_code=status,
                scheduled_start_at=source.fixture.date,
                timezone_iana_name=source.fixture.timezone,
                venue=venue,
                round_name=source.league.round,
            )
        except ValidationError as exc:
            raise PayloadValidationError(_validation_errors(exc)) from exc
        except ValueError as exc:
            raise PayloadValidationError(
                [{"path": "normalization", "message": str(exc), "type": "normalization_error"}]
            ) from exc

    @staticmethod
    def _normalized_venue(value: _ApiFootballVenue | None) -> NormalizedVenue | None:
        if value is None or value.id is None or value.name is None:
            return None
        return NormalizedVenue(provider_id=str(value.id), name=value.name, city=value.city)
