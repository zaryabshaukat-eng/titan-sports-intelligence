"""football-data.org fixture adapter for TITAN's provider-neutral ingestion pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.ingestion.exceptions import PayloadValidationError
from app.modules.ingestion.providers.base import FixtureProviderAdapter
from app.modules.ingestion.providers.football_data_client import FootballDataSeasonContext
from app.modules.ingestion.providers.football_data_country import (
    FootballDataCountryNormalizationError,
    normalize_football_data_country_code,
)
from app.modules.ingestion.schemas import (
    NormalizedCompetition,
    NormalizedCountry,
    NormalizedFixture,
    NormalizedLeague,
    NormalizedSeason,
    NormalizedTeam,
)
from app.modules.sports.enums import CompetitionType, SeasonStatus, TeamType


class _FootballDataArea(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=160)
    code: str = Field(min_length=1, max_length=32)


class _FootballDataCompetition(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = Field(min_length=1, max_length=160)
    code: str = Field(min_length=1, max_length=64)
    type: str = Field(min_length=1, max_length=32)


class _FootballDataSeason(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    startDate: datetime
    endDate: datetime


class _FootballDataTeam(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = Field(min_length=1, max_length=160)
    shortName: str | None = Field(default=None, max_length=64)


class _FootballDataFixturePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    utcDate: datetime
    status: str = Field(min_length=1, max_length=32)
    area: _FootballDataArea
    competition: _FootballDataCompetition
    season: _FootballDataSeason
    homeTeam: _FootballDataTeam
    awayTeam: _FootballDataTeam
    matchday: int | None = Field(default=None, ge=1)
    stage: str | None = Field(default=None, max_length=128)
    group: str | None = Field(default=None, max_length=128)


_STATUS_MAP: dict[str, str] = {
    "SCHEDULED": "scheduled",
    "TIMED": "scheduled",
    "IN_PLAY": "live",
    "EXTRA_TIME": "live",
    "PENALTY_SHOOTOUT": "live",
    "PAUSED": "halftime",
    "FINISHED": "finished",
    "AWARDED": "finished",
    "SUSPENDED": "delayed",
    "POSTPONED": "postponed",
    "CANCELLED": "cancelled",
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


class FootballDataFixtureAdapter(FixtureProviderAdapter):
    """Normalize one football-data.org fixture from a confirmed Premier League season."""

    provider_name = "football_data"

    def __init__(self, season: FootballDataSeasonContext) -> None:
        self._season = season

    def extract_fixture_id(self, payload: dict[str, Any]) -> str | None:
        fixture_id = payload.get("id")
        if not isinstance(fixture_id, int) or isinstance(fixture_id, bool):
            return None
        return str(fixture_id)

    def normalize(self, payload: dict[str, Any]) -> NormalizedFixture:
        try:
            source = _FootballDataFixturePayload.model_validate(payload)
            self._validate_scope(source)
            country_iso_code = normalize_football_data_country_code(source.area.code)
            status = _STATUS_MAP.get(source.status.upper())
            if status is None:
                raise ValueError(f"unsupported football-data.org fixture status '{source.status}'")
            return NormalizedFixture(
                provider_fixture_id=str(source.id),
                sport="football",
                country=NormalizedCountry(
                    provider_id=source.area.code,
                    name=source.area.name,
                    iso_code=country_iso_code,
                ),
                league=NormalizedLeague(
                    provider_id=str(source.competition.id),
                    name=source.competition.name,
                    short_name=source.competition.code,
                ),
                competition=NormalizedCompetition(
                    provider_id=str(source.competition.id),
                    name=source.competition.name,
                    short_name=source.competition.code,
                    competition_type=CompetitionType.LEAGUE,
                ),
                season=NormalizedSeason(
                    provider_id=str(source.season.id),
                    name=self._season_name(source.season.startDate, source.season.endDate),
                    start_date=source.season.startDate.date(),
                    end_date=source.season.endDate.date(),
                    status=SeasonStatus.ACTIVE,
                ),
                home_team=NormalizedTeam(
                    provider_id=str(source.homeTeam.id),
                    name=source.homeTeam.name,
                    short_name=source.homeTeam.shortName,
                    team_type=TeamType.CLUB,
                ),
                away_team=NormalizedTeam(
                    provider_id=str(source.awayTeam.id),
                    name=source.awayTeam.name,
                    short_name=source.awayTeam.shortName,
                    team_type=TeamType.CLUB,
                ),
                fixture_status_code=status,
                scheduled_start_at=source.utcDate,
                timezone_iana_name="UTC",
                round_name=str(source.matchday) if source.matchday is not None else None,
                stage_name=self._stage_name(source.stage, source.group),
            )
        except ValidationError as exc:
            raise PayloadValidationError(_validation_errors(exc)) from exc
        except (FootballDataCountryNormalizationError, ValueError) as exc:
            raise PayloadValidationError(
                [{"path": "normalization", "message": str(exc), "type": "normalization_error"}]
            ) from exc

    def _validate_scope(self, source: _FootballDataFixturePayload) -> None:
        if source.competition.id != self._season.competition_id:
            raise ValueError("fixture competition does not match the confirmed import competition")
        if source.competition.code != self._season.competition_code:
            raise ValueError(
                "fixture competition code does not match the confirmed import competition"
            )
        if source.season.id != self._season.season_id:
            raise ValueError("fixture season does not match the confirmed import season")
        if source.area.code != self._season.country_provider_code:
            raise ValueError("fixture country does not match the confirmed import country")

    @staticmethod
    def _season_name(start_date: datetime, end_date: datetime) -> str:
        return f"{start_date.year}/{end_date.year % 100:02d}"

    @staticmethod
    def _stage_name(stage: str | None, group: str | None) -> str | None:
        if stage is None:
            return group
        return f"{stage} / {group}" if group is not None else stage
