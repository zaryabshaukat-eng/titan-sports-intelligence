"""API facade preserving Sports repository behavior without route coupling."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sports.models import (
    Competition,
    Country,
    Fixture,
    FixtureStatus,
    League,
    Official,
    Season,
    Team,
    Timezone,
    Venue,
)
from app.modules.sports.repositories import (
    CompetitionRepository,
    CountryRepository,
    FixtureRepository,
    FixtureStatusRepository,
    LeagueRepository,
    OfficialRepository,
    PageResult,
    SeasonRepository,
    TeamRepository,
    TimezoneRepository,
    VenueRepository,
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


class SportsApiFacade:
    """One-for-one adapter; no business rules, filtering, or DTO changes live here."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def countries(
        self, filters: CountryFilters, page: PaginationParams
    ) -> PageResult[Country]:
        return await CountryRepository(self._session).list(filters, page)

    async def country(self, id: UUID) -> Country | None:
        return await CountryRepository(self._session).get(id)

    async def leagues(self, filters: LeagueFilters, page: PaginationParams) -> PageResult[League]:
        return await LeagueRepository(self._session).list(filters, page)

    async def league(self, id: UUID) -> League | None:
        return await LeagueRepository(self._session).get(id)

    async def competitions(
        self, filters: CompetitionFilters, page: PaginationParams
    ) -> PageResult[Competition]:
        return await CompetitionRepository(self._session).list(filters, page)

    async def competition(self, id: UUID) -> Competition | None:
        return await CompetitionRepository(self._session).get(id)

    async def seasons(self, filters: SeasonFilters, page: PaginationParams) -> PageResult[Season]:
        return await SeasonRepository(self._session).list(filters, page)

    async def season(self, id: UUID) -> Season | None:
        return await SeasonRepository(self._session).get(id)

    async def teams(self, filters: TeamFilters, page: PaginationParams) -> PageResult[Team]:
        return await TeamRepository(self._session).list(filters, page)

    async def team(self, id: UUID) -> Team | None:
        return await TeamRepository(self._session).get(id)

    async def venues(self, filters: VenueFilters, page: PaginationParams) -> PageResult[Venue]:
        return await VenueRepository(self._session).list(filters, page)

    async def venue(self, id: UUID) -> Venue | None:
        return await VenueRepository(self._session).get(id)

    async def timezones(
        self, filters: TimezoneFilters, page: PaginationParams
    ) -> PageResult[Timezone]:
        return await TimezoneRepository(self._session).list(filters, page)

    async def timezone(self, id: UUID) -> Timezone | None:
        return await TimezoneRepository(self._session).get(id)

    async def fixture_statuses(self, page: PaginationParams) -> PageResult[FixtureStatus]:
        return await FixtureStatusRepository(self._session).list(page)

    async def fixture_status(self, id: UUID) -> FixtureStatus | None:
        return await FixtureStatusRepository(self._session).get(id)

    async def fixtures(
        self, filters: FixtureFilters, page: PaginationParams
    ) -> PageResult[Fixture]:
        return await FixtureRepository(self._session).list(filters, page)

    async def fixture(self, id: UUID) -> Fixture | None:
        return await FixtureRepository(self._session).get(id)

    async def officials(
        self, filters: OfficialFilters, page: PaginationParams
    ) -> PageResult[Official]:
        return await OfficialRepository(self._session).list(filters, page)

    async def official(self, id: UUID) -> Official | None:
        return await OfficialRepository(self._session).get(id)
