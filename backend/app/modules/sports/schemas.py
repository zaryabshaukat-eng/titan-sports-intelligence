"""Read contracts and validated query parameters for the canonical Sports API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.sports.enums import CompetitionType, SeasonStatus, TeamType


class ReadSchema(BaseModel):
    """Base response contract supporting direct conversion from SQLAlchemy entities."""

    model_config = ConfigDict(from_attributes=True)


class AuditReadSchema(ReadSchema):
    """Common identity and immutable audit timestamps exposed by every entity."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class SoftDeletedReadSchema(AuditReadSchema):
    """Common response fields for soft-deletable master data."""

    deleted_at: datetime | None


class CountryRead(SoftDeletedReadSchema):
    name: str
    iso_code: str
    iso3_code: str | None
    primary_timezone_id: UUID | None


class LeagueRead(SoftDeletedReadSchema):
    name: str
    short_name: str | None
    sport: str
    country_id: UUID | None


class CompetitionRead(SoftDeletedReadSchema):
    name: str
    short_name: str | None
    sport: str
    competition_type: CompetitionType
    league_id: UUID | None
    country_id: UUID | None
    default_timezone_id: UUID | None


class SeasonRead(SoftDeletedReadSchema):
    competition_id: UUID
    name: str
    start_date: date
    end_date: date
    status: SeasonStatus


class TeamRead(SoftDeletedReadSchema):
    name: str
    short_name: str | None
    sport: str
    team_type: TeamType
    founded_year: int | None
    country_id: UUID | None
    home_venue_id: UUID | None


class VenueRead(SoftDeletedReadSchema):
    name: str
    city: str | None
    address: str | None
    capacity: int | None
    country_id: UUID | None
    timezone_id: UUID | None


class TimezoneRead(AuditReadSchema):
    iana_name: str
    display_name: str
    is_active: bool


class FixtureStatusRead(AuditReadSchema):
    code: str
    name: str
    description: str | None
    is_terminal: bool
    sort_order: int


class FixtureRead(AuditReadSchema):
    season_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    fixture_status_id: UUID
    venue_id: UUID | None
    timezone_id: UUID | None
    scheduled_start_at: datetime
    scheduled_end_at: datetime | None
    round_name: str | None
    stage_name: str | None


class OfficialRead(SoftDeletedReadSchema):
    full_name: str
    country_id: UUID | None


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Stable offset-pagination envelope shared by all list endpoints."""

    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class PaginationParams(BaseModel):
    """Validated bounded pagination accepted by all Sports list endpoints."""

    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CountryFilters(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=128)
    iso_code: str | None = Field(default=None, min_length=2, max_length=2)


class LeagueFilters(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=160)
    country_id: UUID | None = None
    sport: str | None = Field(default=None, min_length=2, max_length=32)


class CompetitionFilters(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=160)
    country_id: UUID | None = None
    league_id: UUID | None = None
    sport: str | None = Field(default=None, min_length=2, max_length=32)
    competition_type: CompetitionType | None = None


class SeasonFilters(BaseModel):
    competition_id: UUID | None = None
    status: SeasonStatus | None = None


class TeamFilters(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=160)
    country_id: UUID | None = None
    sport: str | None = Field(default=None, min_length=2, max_length=32)
    team_type: TeamType | None = None


class VenueFilters(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=160)
    country_id: UUID | None = None
    timezone_id: UUID | None = None


class TimezoneFilters(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=64)
    country_id: UUID | None = None
    is_active: bool | None = None


class FixtureFilters(BaseModel):
    season_id: UUID | None = None
    competition_id: UUID | None = None
    home_team_id: UUID | None = None
    away_team_id: UUID | None = None
    venue_id: UUID | None = None
    fixture_status_id: UUID | None = None
    fixture_status_code: str | None = Field(default=None, min_length=1, max_length=32)
    starts_after: datetime | None = None
    starts_before: datetime | None = None

    @model_validator(mode="after")
    def validate_time_window(self) -> FixtureFilters:
        """Prevent contradictory fixture time windows from reaching the repository."""
        if self.starts_after and self.starts_before and self.starts_after > self.starts_before:
            raise ValueError("starts_after must be earlier than or equal to starts_before")
        return self


class OfficialFilters(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=160)
    country_id: UUID | None = None
