"""Provider-neutral normalized fixture contracts and ingestion API schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.ingestion.enums import IngestionAuditOutcome
from app.modules.sports.enums import CompetitionType, OfficialRole, SeasonStatus, TeamType


class NormalizedEntity(BaseModel):
    """Provider identity and display attributes for a canonical master entity."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=160)


class NormalizedCountry(NormalizedEntity):
    """Country data normalized to ISO 3166 identifiers."""

    iso_code: str = Field(min_length=2, max_length=2)
    iso3_code: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("iso_code", "iso3_code")
    @classmethod
    def normalize_iso_code(cls, value: str | None) -> str | None:
        """Keep country natural keys compatible with canonical database constraints."""
        return value.upper() if value is not None else None


class NormalizedLeague(NormalizedEntity):
    """A provider-neutral league organization."""

    short_name: str | None = Field(default=None, max_length=64)


class NormalizedCompetition(NormalizedEntity):
    """A competition owned by a league or independent organizer."""

    short_name: str | None = Field(default=None, max_length=64)
    competition_type: CompetitionType


class NormalizedSeason(NormalizedEntity):
    """Bounded competition season metadata."""

    start_date: date
    end_date: date
    status: SeasonStatus

    @model_validator(mode="after")
    def validate_date_range(self) -> NormalizedSeason:
        """Reject impossible seasons before any persistence occurs."""
        if self.start_date > self.end_date:
            raise ValueError("season start_date must be on or before end_date")
        return self


class NormalizedTeam(NormalizedEntity):
    """Canonical attributes required to identify a competing team."""

    short_name: str | None = Field(default=None, max_length=64)
    team_type: TeamType
    country_iso_code: str | None = Field(default=None, min_length=2, max_length=2)
    founded_year: int | None = Field(default=None, ge=1, le=9999)

    @field_validator("country_iso_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        """Normalize optional team country references for canonical lookup."""
        return value.upper() if value is not None else None


class NormalizedVenue(NormalizedEntity):
    """Optional physical fixture venue."""

    city: str | None = Field(default=None, max_length=128)
    address: str | None = Field(default=None, max_length=2000)
    capacity: int | None = Field(default=None, ge=0)
    country_iso_code: str | None = Field(default=None, min_length=2, max_length=2)
    timezone_iana_name: str | None = Field(default=None, max_length=64)

    @field_validator("country_iso_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        """Normalize optional venue country references for canonical lookup."""
        return value.upper() if value is not None else None

    @field_validator("timezone_iana_name")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        """Require an IANA zone rather than an ambiguous fixed offset."""
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone_iana_name must be a valid IANA timezone") from exc
        return value


class NormalizedOfficial(NormalizedEntity):
    """Provider-neutral official and assignment attributes."""

    role: OfficialRole
    assignment_order: int = Field(default=0, ge=0, le=32767)
    country_iso_code: str | None = Field(default=None, min_length=2, max_length=2)

    @field_validator("country_iso_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        """Normalize optional official country references for canonical lookup."""
        return value.upper() if value is not None else None


class NormalizedFixture(BaseModel):
    """Canonical fixture candidate emitted by every provider adapter."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider_fixture_id: str = Field(min_length=1, max_length=128)
    sport: str = Field(min_length=2, max_length=32)
    country: NormalizedCountry
    league: NormalizedLeague
    competition: NormalizedCompetition
    season: NormalizedSeason
    home_team: NormalizedTeam
    away_team: NormalizedTeam
    fixture_status_code: str = Field(min_length=1, max_length=32)
    scheduled_start_at: datetime
    scheduled_end_at: datetime | None = None
    timezone_iana_name: str = Field(min_length=3, max_length=64)
    venue: NormalizedVenue | None = None
    round_name: str | None = Field(default=None, max_length=128)
    stage_name: str | None = Field(default=None, max_length=128)
    officials: list[NormalizedOfficial] = Field(default_factory=list, max_length=32)

    @field_validator("sport", "fixture_status_code")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        """Use lowercase controlled values for comparisons and status lookup."""
        return value.lower()

    @field_validator("timezone_iana_name")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Validate canonical timezone values independently of provider vocabulary."""
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone_iana_name must be a valid IANA timezone") from exc
        return value

    @field_validator("scheduled_start_at", "scheduled_end_at")
    @classmethod
    def require_timezone_aware(cls, value: datetime | None) -> datetime | None:
        """Prevent an adapter from sending an ambiguous local kickoff time."""
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("fixture timestamps must include a timezone offset")
        return value

    @model_validator(mode="after")
    def validate_fixture_invariants(self) -> NormalizedFixture:
        """Check invariants that span the full normalized fixture."""
        if self.home_team.provider_id == self.away_team.provider_id:
            raise ValueError("home_team and away_team must be distinct")
        if self.scheduled_end_at is not None and self.scheduled_end_at < self.scheduled_start_at:
            raise ValueError("scheduled_end_at must be on or after scheduled_start_at")
        official_ids = [official.provider_id for official in self.officials]
        if len(official_ids) != len(set(official_ids)):
            raise ValueError("official provider identities must be unique within a fixture")
        official_slots = [(official.role, official.assignment_order) for official in self.officials]
        if len(official_slots) != len(set(official_slots)):
            raise ValueError("official role and assignment order combinations must be unique")
        return self


class FixtureIngestionRequest(BaseModel):
    """Protected internal API request containing provider-owned JSON payloads."""

    payloads: list[dict[str, Any]] = Field(min_length=1, max_length=500)


class FixtureIngestionItemResult(BaseModel):
    """Per-payload processing result without echoing sensitive provider JSON."""

    source_index: int = Field(ge=0)
    outcome: IngestionAuditOutcome
    fixture_id: UUID | None = None
    validation_errors: list[dict[str, Any]] | None = None


class FixtureIngestionBatchResult(BaseModel):
    """Batch result emitted after the request-scoped database transaction commits."""

    run_id: UUID
    provider_name: str
    received_count: int = Field(ge=0)
    inserted_count: int = Field(ge=0)
    updated_count: int = Field(ge=0)
    unchanged_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    items: list[FixtureIngestionItemResult]
