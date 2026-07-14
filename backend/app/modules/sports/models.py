"""Canonical, provider-neutral SQLAlchemy entities for organized sport."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.sports.enums import CompetitionType, OfficialRole, SeasonStatus, TeamType
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    """Application-assigned UUID identity suitable for distributed ingestion later."""

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    """Record creation and last-update timestamps in UTC-aware database columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Retain master-record history while removing entities from default reads."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Timezone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """IANA timezone identity; offsets are deliberately not stored because of DST."""

    __tablename__ = "sports_timezones"
    __table_args__ = (
        CheckConstraint("char_length(iana_name) >= 3", name="ck_sports_timezones_iana_name_length"),
    )

    iana_name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    countries: Mapped[list[Country]] = relationship(
        back_populates="primary_timezone", foreign_keys="Country.primary_timezone_id"
    )
    venues: Mapped[list[Venue]] = relationship(back_populates="timezone")
    competitions: Mapped[list[Competition]] = relationship(back_populates="default_timezone")
    fixtures: Mapped[list[Fixture]] = relationship(back_populates="timezone")


class Country(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Canonical country reference identified by ISO 3166 codes."""

    __tablename__ = "sports_countries"
    __table_args__ = (
        CheckConstraint("char_length(iso_code) = 2", name="ck_sports_countries_iso_code_length"),
        CheckConstraint("iso_code = upper(iso_code)", name="ck_sports_countries_iso_code_upper"),
        CheckConstraint("iso3_code = upper(iso3_code)", name="ck_sports_countries_iso3_code_upper"),
        UniqueConstraint("iso3_code", name="uq_sports_countries_iso3_code"),
        Index("ix_sports_countries_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    iso_code: Mapped[str] = mapped_column(String(2), nullable=False, unique=True, index=True)
    iso3_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    primary_timezone_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_timezones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    primary_timezone: Mapped[Timezone | None] = relationship(
        back_populates="countries", foreign_keys=[primary_timezone_id]
    )
    leagues: Mapped[list[League]] = relationship(back_populates="country")
    teams: Mapped[list[Team]] = relationship(back_populates="country")
    venues: Mapped[list[Venue]] = relationship(back_populates="country")
    competitions: Mapped[list[Competition]] = relationship(back_populates="country")
    officials: Mapped[list[Official]] = relationship(back_populates="country")


class League(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A durable league organization which may parent multiple competitions."""

    __tablename__ = "sports_leagues"
    __table_args__ = (
        UniqueConstraint(
            "country_id", "sport", "name", name="uq_sports_leagues_country_sport_name"
        ),
        CheckConstraint("char_length(sport) >= 2", name="ck_sports_leagues_sport_length"),
        Index("ix_sports_leagues_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sport: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    country_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_countries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    country: Mapped[Country | None] = relationship(back_populates="leagues")
    competitions: Mapped[list[Competition]] = relationship(back_populates="league")


class Competition(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A provider-neutral competition such as a league season, cup, or tournament."""

    __tablename__ = "sports_competitions"
    __table_args__ = (
        UniqueConstraint("league_id", "name", name="uq_sports_competitions_league_name"),
        CheckConstraint("char_length(sport) >= 2", name="ck_sports_competitions_sport_length"),
        Index("ix_sports_competitions_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sport: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    competition_type: Mapped[CompetitionType] = mapped_column(
        SqlEnum(CompetitionType, name="sports_competition_type"), nullable=False, index=True
    )
    league_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_leagues.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    country_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_countries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    default_timezone_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_timezones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    league: Mapped[League | None] = relationship(back_populates="competitions")
    country: Mapped[Country | None] = relationship(back_populates="competitions")
    default_timezone: Mapped[Timezone | None] = relationship(back_populates="competitions")
    seasons: Mapped[list[Season]] = relationship(back_populates="competition")


class Season(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A bounded time period of a competition."""

    __tablename__ = "sports_seasons"
    __table_args__ = (
        UniqueConstraint("competition_id", "name", name="uq_sports_seasons_competition_name"),
        CheckConstraint("start_date <= end_date", name="ck_sports_seasons_date_range"),
        Index("ix_sports_seasons_deleted_at", "deleted_at"),
        Index("ix_sports_seasons_status", "status"),
    )

    competition_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_competitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SeasonStatus] = mapped_column(
        SqlEnum(SeasonStatus, name="sports_season_status"), nullable=False, index=True
    )

    competition: Mapped[Competition] = relationship(back_populates="seasons")
    fixtures: Mapped[list[Fixture]] = relationship(back_populates="season")


class Venue(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A physical venue at which fixtures may be scheduled."""

    __tablename__ = "sports_venues"
    __table_args__ = (
        UniqueConstraint("country_id", "name", name="uq_sports_venues_country_name"),
        CheckConstraint("capacity IS NULL OR capacity >= 0", name="ck_sports_venues_capacity"),
        Index("ix_sports_venues_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_countries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    timezone_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_timezones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    country: Mapped[Country | None] = relationship(back_populates="venues")
    timezone: Mapped[Timezone | None] = relationship(back_populates="venues")
    home_teams: Mapped[list[Team]] = relationship(back_populates="home_venue")
    fixtures: Mapped[list[Fixture]] = relationship(back_populates="venue")


class Team(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A canonical club, national, representative, or other competing team."""

    __tablename__ = "sports_teams"
    __table_args__ = (
        UniqueConstraint("country_id", "sport", "name", name="uq_sports_teams_country_sport_name"),
        CheckConstraint(
            "founded_year IS NULL OR founded_year > 0", name="ck_sports_teams_founded_year"
        ),
        CheckConstraint("char_length(sport) >= 2", name="ck_sports_teams_sport_length"),
        Index("ix_sports_teams_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sport: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    team_type: Mapped[TeamType] = mapped_column(
        SqlEnum(TeamType, name="sports_team_type"), nullable=False, index=True
    )
    founded_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    country_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_countries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    home_venue_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_venues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    country: Mapped[Country | None] = relationship(back_populates="teams")
    home_venue: Mapped[Venue | None] = relationship(back_populates="home_teams")
    home_fixtures: Mapped[list[Fixture]] = relationship(
        back_populates="home_team", foreign_keys="Fixture.home_team_id"
    )
    away_fixtures: Mapped[list[Fixture]] = relationship(
        back_populates="away_team", foreign_keys="Fixture.away_team_id"
    )


class FixtureStatus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Extensible canonical fixture-state taxonomy, separate from provider labels."""

    __tablename__ = "sports_fixture_statuses"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_sports_fixture_statuses_sort_order"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    fixtures: Mapped[list[Fixture]] = relationship(back_populates="fixture_status")
    history_entries: Mapped[list[FixtureStatusHistory]] = relationship(
        back_populates="fixture_status"
    )


class Fixture(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A scheduled or completed contest between two distinct teams in a season."""

    __tablename__ = "sports_fixtures"
    __table_args__ = (
        UniqueConstraint(
            "season_id",
            "home_team_id",
            "away_team_id",
            "scheduled_start_at",
            name="uq_sports_fixtures_season_teams_start",
        ),
        CheckConstraint("home_team_id <> away_team_id", name="ck_sports_fixtures_distinct_teams"),
        Index("ix_sports_fixtures_scheduled_start_at", "scheduled_start_at"),
        Index("ix_sports_fixtures_status_start", "fixture_status_id", "scheduled_start_at"),
    )

    season_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_seasons.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    home_team_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    away_team_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fixture_status_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixture_statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    venue_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_venues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timezone_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_timezones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scheduled_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    round_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    stage_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    season: Mapped[Season] = relationship(back_populates="fixtures")
    home_team: Mapped[Team] = relationship(
        back_populates="home_fixtures", foreign_keys=[home_team_id]
    )
    away_team: Mapped[Team] = relationship(
        back_populates="away_fixtures", foreign_keys=[away_team_id]
    )
    fixture_status: Mapped[FixtureStatus] = relationship(back_populates="fixtures")
    venue: Mapped[Venue | None] = relationship(back_populates="fixtures")
    timezone: Mapped[Timezone | None] = relationship(back_populates="fixtures")
    official_assignments: Mapped[list[FixtureOfficial]] = relationship(back_populates="fixture")
    status_history: Mapped[list[FixtureStatusHistory]] = relationship(back_populates="fixture")


class Official(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A match official, independent of their assignment to any one fixture."""

    __tablename__ = "sports_officials"
    __table_args__ = (Index("ix_sports_officials_deleted_at", "deleted_at"),)

    full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    country_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_countries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    country: Mapped[Country | None] = relationship(back_populates="officials")
    fixture_assignments: Mapped[list[FixtureOfficial]] = relationship(back_populates="official")


class FixtureOfficial(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The role and ordering of an official within one fixture's officiating crew."""

    __tablename__ = "sports_fixture_officials"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id", "official_id", name="uq_sports_fixture_officials_fixture_official"
        ),
        UniqueConstraint(
            "fixture_id",
            "role",
            "assignment_order",
            name="uq_sports_fixture_officials_fixture_role_order",
        ),
        CheckConstraint(
            "assignment_order >= 0", name="ck_sports_fixture_officials_assignment_order"
        ),
    )

    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    official_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_officials.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    role: Mapped[OfficialRole] = mapped_column(
        SqlEnum(OfficialRole, name="sports_official_role"), nullable=False, index=True
    )
    assignment_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    fixture: Mapped[Fixture] = relationship(back_populates="official_assignments")
    official: Mapped[Official] = relationship(back_populates="fixture_assignments")


class FixtureStatusHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only status transitions preserving a fixture's operational history."""

    __tablename__ = "sports_fixture_status_history"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "fixture_status_id",
            "effective_at",
            name="uq_sports_fixture_status_history_transition",
        ),
        Index("ix_sports_fixture_status_history_fixture_effective", "fixture_id", "effective_at"),
    )

    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fixture_status_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixture_statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    fixture: Mapped[Fixture] = relationship(back_populates="status_history")
    fixture_status: Mapped[FixtureStatus] = relationship(back_populates="history_entries")
