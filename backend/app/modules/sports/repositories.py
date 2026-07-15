"""Read repositories for canonical Sports entities.

Repositories own query construction and deliberately return domain entities,
leaving HTTP serialization and status-code decisions to the API adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sports.models import (
    Competition,
    Country,
    CountryTimezone,
    Fixture,
    FixtureStatus,
    League,
    Official,
    Season,
    Team,
    Timezone,
    Venue,
)
from app.modules.sports.schemas import (
    CompetitionFilters,
    CountryFilters,
    FixtureFilters,
    LeagueFilters,
    OfficialFilters,
    PaginationParams,
    SeasonFilters,
    TeamFilters,
    TimezoneFilters,
    VenueFilters,
)


@dataclass(frozen=True, slots=True)
class PageResult[EntityT]:
    """Database-page result independent of an HTTP response schema."""

    items: list[EntityT]
    total: int
    limit: int
    offset: int


class ReadRepository:
    """Shared pagination mechanics for read-only repository implementations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _page[EntityT](
        self, statement: Select[tuple[EntityT]], pagination: PaginationParams
    ) -> PageResult[EntityT]:
        count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
        total = (await self._session.scalar(count_statement)) or 0
        result = await self._session.execute(
            statement.limit(pagination.limit).offset(pagination.offset)
        )
        return PageResult(
            items=list(result.scalars().all()),
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )


class CountryRepository(ReadRepository):
    """Query canonical countries while excluding soft-deleted records."""

    async def list(
        self, filters: CountryFilters, pagination: PaginationParams
    ) -> PageResult[Country]:
        statement = select(Country).where(Country.deleted_at.is_(None))
        if filters.q:
            statement = statement.where(Country.name.ilike(f"%{filters.q}%"))
        if filters.iso_code:
            statement = statement.where(Country.iso_code == filters.iso_code.upper())
        return await self._page(statement.order_by(Country.name), pagination)

    async def get(self, country_id: UUID) -> Country | None:
        return await self._session.scalar(
            select(Country).where(Country.id == country_id, Country.deleted_at.is_(None))
        )


class LeagueRepository(ReadRepository):
    """Query league organizations without exposing deleted master data."""

    async def list(
        self, filters: LeagueFilters, pagination: PaginationParams
    ) -> PageResult[League]:
        statement = select(League).where(League.deleted_at.is_(None))
        if filters.q:
            statement = statement.where(League.name.ilike(f"%{filters.q}%"))
        if filters.country_id:
            statement = statement.where(League.country_id == filters.country_id)
        if filters.sport:
            statement = statement.where(League.sport == filters.sport.lower())
        return await self._page(statement.order_by(League.sport, League.name), pagination)

    async def get(self, league_id: UUID) -> League | None:
        return await self._session.scalar(
            select(League).where(League.id == league_id, League.deleted_at.is_(None))
        )


class CompetitionRepository(ReadRepository):
    """Query canonical competitions and their optional league/country context."""

    async def list(
        self, filters: CompetitionFilters, pagination: PaginationParams
    ) -> PageResult[Competition]:
        statement = select(Competition).where(Competition.deleted_at.is_(None))
        if filters.q:
            statement = statement.where(Competition.name.ilike(f"%{filters.q}%"))
        if filters.country_id:
            statement = statement.where(Competition.country_id == filters.country_id)
        if filters.league_id:
            statement = statement.where(Competition.league_id == filters.league_id)
        if filters.sport:
            statement = statement.where(Competition.sport == filters.sport.lower())
        if filters.competition_type:
            statement = statement.where(Competition.competition_type == filters.competition_type)
        return await self._page(statement.order_by(Competition.sport, Competition.name), pagination)

    async def get(self, competition_id: UUID) -> Competition | None:
        return await self._session.scalar(
            select(Competition).where(
                Competition.id == competition_id, Competition.deleted_at.is_(None)
            )
        )


class SeasonRepository(ReadRepository):
    """Query competition seasons while excluding superseded master records."""

    async def list(
        self, filters: SeasonFilters, pagination: PaginationParams
    ) -> PageResult[Season]:
        statement = select(Season).where(Season.deleted_at.is_(None))
        if filters.competition_id:
            statement = statement.where(Season.competition_id == filters.competition_id)
        if filters.status:
            statement = statement.where(Season.status == filters.status)
        return await self._page(
            statement.order_by(Season.start_date.desc(), Season.name), pagination
        )

    async def get(self, season_id: UUID) -> Season | None:
        return await self._session.scalar(
            select(Season).where(Season.id == season_id, Season.deleted_at.is_(None))
        )


class TeamRepository(ReadRepository):
    """Query canonical teams without exposing deleted master records."""

    async def list(self, filters: TeamFilters, pagination: PaginationParams) -> PageResult[Team]:
        statement = select(Team).where(Team.deleted_at.is_(None))
        if filters.q:
            statement = statement.where(Team.name.ilike(f"%{filters.q}%"))
        if filters.country_id:
            statement = statement.where(Team.country_id == filters.country_id)
        if filters.sport:
            statement = statement.where(Team.sport == filters.sport.lower())
        if filters.team_type:
            statement = statement.where(Team.team_type == filters.team_type)
        return await self._page(statement.order_by(Team.sport, Team.name), pagination)

    async def get(self, team_id: UUID) -> Team | None:
        return await self._session.scalar(
            select(Team).where(Team.id == team_id, Team.deleted_at.is_(None))
        )


class VenueRepository(ReadRepository):
    """Query canonical venues without exposing deleted master records."""

    async def list(self, filters: VenueFilters, pagination: PaginationParams) -> PageResult[Venue]:
        statement = select(Venue).where(Venue.deleted_at.is_(None))
        if filters.q:
            statement = statement.where(Venue.name.ilike(f"%{filters.q}%"))
        if filters.country_id:
            statement = statement.where(Venue.country_id == filters.country_id)
        if filters.timezone_id:
            statement = statement.where(Venue.timezone_id == filters.timezone_id)
        return await self._page(statement.order_by(Venue.name), pagination)

    async def get(self, venue_id: UUID) -> Venue | None:
        return await self._session.scalar(
            select(Venue).where(Venue.id == venue_id, Venue.deleted_at.is_(None))
        )


class TimezoneRepository(ReadRepository):
    """Query active IANA timezones and their country reference usage."""

    async def list(
        self, filters: TimezoneFilters, pagination: PaginationParams
    ) -> PageResult[Timezone]:
        statement = select(Timezone)
        if filters.q:
            statement = statement.where(Timezone.iana_name.ilike(f"%{filters.q}%"))
        if filters.country_id:
            statement = (
                statement.join(CountryTimezone, CountryTimezone.timezone_id == Timezone.id)
                .join(Country, Country.id == CountryTimezone.country_id)
                .where(
                    Country.id == filters.country_id,
                    Country.deleted_at.is_(None),
                )
            )
        if filters.is_active is not None:
            statement = statement.where(Timezone.is_active == filters.is_active)
        return await self._page(statement.order_by(Timezone.iana_name), pagination)

    async def get(self, timezone_id: UUID) -> Timezone | None:
        return await self._session.scalar(select(Timezone).where(Timezone.id == timezone_id))


class FixtureStatusRepository(ReadRepository):
    """Query the stable, extensible fixture-status taxonomy."""

    async def list(self, pagination: PaginationParams) -> PageResult[FixtureStatus]:
        return await self._page(
            select(FixtureStatus).order_by(FixtureStatus.sort_order, FixtureStatus.code), pagination
        )

    async def get(self, status_id: UUID) -> FixtureStatus | None:
        return await self._session.scalar(
            select(FixtureStatus).where(FixtureStatus.id == status_id)
        )


class FixtureRepository(ReadRepository):
    """Query immutable fixture records and canonical scheduling dimensions."""

    async def list(
        self, filters: FixtureFilters, pagination: PaginationParams
    ) -> PageResult[Fixture]:
        statement = select(Fixture)
        if filters.competition_id:
            statement = statement.join(Season).where(
                Season.competition_id == filters.competition_id
            )
        if filters.season_id:
            statement = statement.where(Fixture.season_id == filters.season_id)
        if filters.home_team_id:
            statement = statement.where(Fixture.home_team_id == filters.home_team_id)
        if filters.away_team_id:
            statement = statement.where(Fixture.away_team_id == filters.away_team_id)
        if filters.venue_id:
            statement = statement.where(Fixture.venue_id == filters.venue_id)
        if filters.fixture_status_id:
            statement = statement.where(Fixture.fixture_status_id == filters.fixture_status_id)
        if filters.fixture_status_code:
            statement = statement.join(FixtureStatus).where(
                FixtureStatus.code == filters.fixture_status_code.lower()
            )
        if filters.starts_after:
            statement = statement.where(Fixture.scheduled_start_at >= filters.starts_after)
        if filters.starts_before:
            statement = statement.where(Fixture.scheduled_start_at <= filters.starts_before)
        return await self._page(statement.order_by(Fixture.scheduled_start_at), pagination)

    async def get(self, fixture_id: UUID) -> Fixture | None:
        return await self._session.scalar(select(Fixture).where(Fixture.id == fixture_id))


class OfficialRepository(ReadRepository):
    """Query canonical officials without exposing deleted master records."""

    async def list(
        self, filters: OfficialFilters, pagination: PaginationParams
    ) -> PageResult[Official]:
        statement = select(Official).where(Official.deleted_at.is_(None))
        if filters.q:
            statement = statement.where(Official.full_name.ilike(f"%{filters.q}%"))
        if filters.country_id:
            statement = statement.where(Official.country_id == filters.country_id)
        return await self._page(statement.order_by(Official.full_name), pagination)

    async def get(self, official_id: UUID) -> Official | None:
        return await self._session.scalar(
            select(Official).where(Official.id == official_id, Official.deleted_at.is_(None))
        )
