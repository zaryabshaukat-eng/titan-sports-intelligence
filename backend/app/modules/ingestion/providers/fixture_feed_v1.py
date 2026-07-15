"""Reference adapter for the documented ``fixture_feed_v1`` provider contract.

The provider-specific request DTOs live here, deliberately separate from the
provider-neutral normalized contracts consumed by the ingestion service.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.ingestion.exceptions import PayloadValidationError
from app.modules.ingestion.providers.base import FixtureProviderAdapter
from app.modules.ingestion.schemas import (
    NormalizedCompetition,
    NormalizedCountry,
    NormalizedFixture,
    NormalizedLeague,
    NormalizedOfficial,
    NormalizedSeason,
    NormalizedTeam,
    NormalizedVenue,
)
from app.modules.sports.enums import CompetitionType, OfficialRole, SeasonStatus, TeamType


class FixtureFeedV1Entity(BaseModel):
    """Provider's common entity shape, intentionally scoped to this adapter."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=160)
    short_name: str | None = Field(default=None, max_length=64)


class FixtureFeedV1Country(FixtureFeedV1Entity):
    """Provider country vocabulary."""

    iso_code: str = Field(min_length=2, max_length=2)
    iso3_code: str | None = Field(default=None, min_length=3, max_length=3)


class FixtureFeedV1Competition(FixtureFeedV1Entity):
    """Provider competition vocabulary."""

    type: str = Field(min_length=1, max_length=32)


class FixtureFeedV1Season(FixtureFeedV1Entity):
    """Provider season vocabulary."""

    start_date: date
    end_date: date
    status: str = Field(min_length=1, max_length=32)


class FixtureFeedV1Team(FixtureFeedV1Entity):
    """Provider team vocabulary."""

    type: str = Field(min_length=1, max_length=32)
    country_iso_code: str | None = Field(default=None, min_length=2, max_length=2)
    founded_year: int | None = Field(default=None, ge=1, le=9999)


class FixtureFeedV1Venue(FixtureFeedV1Entity):
    """Provider venue vocabulary."""

    city: str | None = Field(default=None, max_length=128)
    address: str | None = Field(default=None, max_length=2000)
    capacity: int | None = Field(default=None, ge=0)
    country_iso_code: str | None = Field(default=None, min_length=2, max_length=2)
    timezone: str | None = Field(default=None, max_length=64)


class FixtureFeedV1Official(FixtureFeedV1Entity):
    """Provider official-assignment vocabulary."""

    role: str = Field(min_length=1, max_length=32)
    assignment_order: int = Field(default=0, ge=0, le=32767)
    country_iso_code: str | None = Field(default=None, min_length=2, max_length=2)


class FixtureFeedV1Fixture(BaseModel):
    """Provider fixture fields, including source-specific status labels."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=128)
    kickoff: datetime
    scheduled_end: datetime | None = None
    status: str = Field(min_length=1, max_length=64)
    timezone: str = Field(min_length=3, max_length=64)
    round: str | None = Field(default=None, max_length=128)
    stage: str | None = Field(default=None, max_length=128)
    venue: FixtureFeedV1Venue | None = None


class FixtureFeedV1Teams(BaseModel):
    """Provider's home/away participant container."""

    model_config = ConfigDict(extra="ignore")

    home: FixtureFeedV1Team
    away: FixtureFeedV1Team


class FixtureFeedV1Payload(BaseModel):
    """Complete fixture JSON schema expected by the reference provider."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    fixture: FixtureFeedV1Fixture
    sport: str = Field(min_length=2, max_length=32)
    country: FixtureFeedV1Country
    league: FixtureFeedV1Entity
    competition: FixtureFeedV1Competition
    season: FixtureFeedV1Season
    teams: FixtureFeedV1Teams
    officials: list[FixtureFeedV1Official] = Field(default_factory=list, max_length=32)


_STATUS_MAP: dict[str, str] = {
    "scheduled": "scheduled",
    "not_started": "scheduled",
    "delayed": "delayed",
    "postponed": "postponed",
    "live": "live",
    "in_progress": "live",
    "halftime": "halftime",
    "finished": "finished",
    "completed": "finished",
    "cancelled": "cancelled",
    "abandoned": "abandoned",
}
_OFFICIAL_ROLE_MAP: dict[str, OfficialRole] = {
    "referee": OfficialRole.REFEREE,
    "assistant_referee": OfficialRole.ASSISTANT_REFEREE,
    "assistant": OfficialRole.ASSISTANT_REFEREE,
    "fourth_official": OfficialRole.FOURTH_OFFICIAL,
    "fourth": OfficialRole.FOURTH_OFFICIAL,
    "video_assistant": OfficialRole.VIDEO_ASSISTANT,
    "var": OfficialRole.VIDEO_ASSISTANT,
    "other": OfficialRole.OTHER,
}


def _validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
    """Convert Pydantic errors to stable, audit-safe structured validation diagnostics."""
    return [
        {
            "path": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors(include_input=False)
    ]


class FixtureFeedV1Adapter(FixtureProviderAdapter):
    """Normalize the explicit reference provider feed without leaking its fields downstream."""

    provider_name = "fixture_feed_v1"

    def extract_fixture_id(self, payload: dict[str, Any]) -> str | None:
        """Return a best-effort ID even when complete DTO validation fails."""
        fixture = payload.get("fixture")
        if not isinstance(fixture, dict):
            return None
        fixture_id = fixture.get("id")
        if fixture_id is None:
            return None
        normalized = str(fixture_id)
        return normalized if 1 <= len(normalized) <= 128 else None

    def normalize(self, payload: dict[str, Any]) -> NormalizedFixture:
        """Validate provider JSON then map its vocabulary to canonical TITAN concepts."""
        try:
            source = FixtureFeedV1Payload.model_validate(payload)
            status_code = _STATUS_MAP[source.fixture.status.lower()]
            official_models = [
                NormalizedOfficial(
                    provider_id=official.id,
                    name=official.name,
                    role=_OFFICIAL_ROLE_MAP.get(official.role.lower(), OfficialRole.OTHER),
                    assignment_order=official.assignment_order,
                    country_iso_code=official.country_iso_code,
                )
                for official in source.officials
            ]
            venue = (
                NormalizedVenue(
                    provider_id=source.fixture.venue.id,
                    name=source.fixture.venue.name,
                    city=source.fixture.venue.city,
                    address=source.fixture.venue.address,
                    capacity=source.fixture.venue.capacity,
                    country_iso_code=source.fixture.venue.country_iso_code,
                    timezone_iana_name=source.fixture.venue.timezone,
                )
                if source.fixture.venue is not None
                else None
            )
            return NormalizedFixture(
                provider_fixture_id=source.fixture.id,
                sport=source.sport,
                country=NormalizedCountry(
                    provider_id=source.country.id,
                    name=source.country.name,
                    iso_code=source.country.iso_code,
                    iso3_code=source.country.iso3_code,
                ),
                league=NormalizedLeague(
                    provider_id=source.league.id,
                    name=source.league.name,
                    short_name=source.league.short_name,
                ),
                competition=NormalizedCompetition(
                    provider_id=source.competition.id,
                    name=source.competition.name,
                    short_name=source.competition.short_name,
                    competition_type=CompetitionType(source.competition.type.lower()),
                ),
                season=NormalizedSeason(
                    provider_id=source.season.id,
                    name=source.season.name,
                    start_date=source.season.start_date,
                    end_date=source.season.end_date,
                    status=SeasonStatus(source.season.status.lower()),
                ),
                home_team=NormalizedTeam(
                    provider_id=source.teams.home.id,
                    name=source.teams.home.name,
                    short_name=source.teams.home.short_name,
                    team_type=TeamType(source.teams.home.type.lower()),
                    country_iso_code=source.teams.home.country_iso_code,
                    founded_year=source.teams.home.founded_year,
                ),
                away_team=NormalizedTeam(
                    provider_id=source.teams.away.id,
                    name=source.teams.away.name,
                    short_name=source.teams.away.short_name,
                    team_type=TeamType(source.teams.away.type.lower()),
                    country_iso_code=source.teams.away.country_iso_code,
                    founded_year=source.teams.away.founded_year,
                ),
                fixture_status_code=status_code,
                scheduled_start_at=source.fixture.kickoff,
                scheduled_end_at=source.fixture.scheduled_end,
                timezone_iana_name=source.fixture.timezone,
                venue=venue,
                round_name=source.fixture.round,
                stage_name=source.fixture.stage,
                officials=official_models,
            )
        except KeyError as exc:
            raise PayloadValidationError(
                [
                    {
                        "path": "fixture.status",
                        "message": f"unsupported provider fixture status '{exc.args[0]}'",
                        "type": "unsupported_status",
                    }
                ]
            ) from exc
        except ValidationError as exc:
            raise PayloadValidationError(_validation_errors(exc)) from exc
        except ValueError as exc:
            raise PayloadValidationError(
                [{"path": "normalization", "message": str(exc), "type": "normalization_error"}]
            ) from exc
