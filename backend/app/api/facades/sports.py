"""API facade preserving Sports repository behavior without route coupling."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sports.repositories import (
    CompetitionRepository,
    CountryRepository,
    FixtureRepository,
    FixtureStatusRepository,
    LeagueRepository,
    OfficialRepository,
    SeasonRepository,
    TeamRepository,
    TimezoneRepository,
    VenueRepository,
)


class SportsApiFacade:
    """One-for-one adapter; no business rules, filtering, or DTO changes live here."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def countries(self, filters: object, page: object):
        return await CountryRepository(self._session).list(filters, page)

    async def country(self, id: UUID):
        return await CountryRepository(self._session).get(id)

    async def leagues(self, filters: object, page: object):
        return await LeagueRepository(self._session).list(filters, page)

    async def league(self, id: UUID):
        return await LeagueRepository(self._session).get(id)

    async def competitions(self, filters: object, page: object):
        return await CompetitionRepository(self._session).list(filters, page)

    async def competition(self, id: UUID):
        return await CompetitionRepository(self._session).get(id)

    async def seasons(self, filters: object, page: object):
        return await SeasonRepository(self._session).list(filters, page)

    async def season(self, id: UUID):
        return await SeasonRepository(self._session).get(id)

    async def teams(self, filters: object, page: object):
        return await TeamRepository(self._session).list(filters, page)

    async def team(self, id: UUID):
        return await TeamRepository(self._session).get(id)

    async def venues(self, filters: object, page: object):
        return await VenueRepository(self._session).list(filters, page)

    async def venue(self, id: UUID):
        return await VenueRepository(self._session).get(id)

    async def timezones(self, filters: object, page: object):
        return await TimezoneRepository(self._session).list(filters, page)

    async def timezone(self, id: UUID):
        return await TimezoneRepository(self._session).get(id)

    async def fixture_statuses(self, page: object):
        return await FixtureStatusRepository(self._session).list(page)

    async def fixture_status(self, id: UUID):
        return await FixtureStatusRepository(self._session).get(id)

    async def fixtures(self, filters: object, page: object):
        return await FixtureRepository(self._session).list(filters, page)

    async def fixture(self, id: UUID):
        return await FixtureRepository(self._session).get(id)

    async def officials(self, filters: object, page: object):
        return await OfficialRepository(self._session).list(filters, page)

    async def official(self, id: UUID):
        return await OfficialRepository(self._session).get(id)
