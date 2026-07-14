"""Read-only REST adapter for the canonical Sports bounded context."""

from __future__ import annotations

from typing import Annotated, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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
    CompetitionRead,
    CountryFilters,
    CountryRead,
    FixtureFilters,
    FixtureRead,
    FixtureStatusRead,
    LeagueFilters,
    LeagueRead,
    OfficialFilters,
    OfficialRead,
    Page,
    PaginationParams,
    SeasonFilters,
    SeasonRead,
    TeamFilters,
    TeamRead,
    TimezoneFilters,
    TimezoneRead,
    VenueFilters,
    VenueRead,
)
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/sports", tags=["Sports Domain"])

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
PaginationDependency = Annotated[PaginationParams, Depends()]

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def _page(result: PageResult[object], schema: type[SchemaT]) -> Page[SchemaT]:
    """Convert a repository page into its documented public response contract."""
    return Page[SchemaT](
        items=[schema.model_validate(item) for item in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


def _require(entity: SchemaT | None, resource_name: str, resource_id: UUID) -> SchemaT:
    """Return an entity or raise the standardized not-found API response."""
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "sports_resource_not_found",
                "message": f"{resource_name} '{resource_id}' was not found.",
            },
        )
    return entity


@router.get(
    "/countries",
    response_model=Page[CountryRead],
    summary="List canonical countries",
)
async def list_countries(
    filters: Annotated[CountryFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[CountryRead]:
    """List active country reference records with name and ISO filtering."""
    return _page(await CountryRepository(session).list(filters, pagination), CountryRead)


@router.get(
    "/countries/{country_id}", response_model=CountryRead, summary="Get a canonical country"
)
async def get_country(country_id: UUID, session: SessionDependency) -> CountryRead:
    """Fetch one non-deleted country by its canonical UUID."""
    country = _require(await CountryRepository(session).get(country_id), "Country", country_id)
    return CountryRead.model_validate(country)


@router.get("/leagues", response_model=Page[LeagueRead], summary="List canonical leagues")
async def list_leagues(
    filters: Annotated[LeagueFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[LeagueRead]:
    """List active league organizations by country, sport, or name."""
    return _page(await LeagueRepository(session).list(filters, pagination), LeagueRead)


@router.get("/leagues/{league_id}", response_model=LeagueRead, summary="Get a canonical league")
async def get_league(league_id: UUID, session: SessionDependency) -> LeagueRead:
    """Fetch one non-deleted league by its canonical UUID."""
    league = _require(await LeagueRepository(session).get(league_id), "League", league_id)
    return LeagueRead.model_validate(league)


@router.get(
    "/competitions",
    response_model=Page[CompetitionRead],
    summary="List canonical competitions",
)
async def list_competitions(
    filters: Annotated[CompetitionFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[CompetitionRead]:
    """List active competitions by league, country, sport, type, or name."""
    return _page(await CompetitionRepository(session).list(filters, pagination), CompetitionRead)


@router.get(
    "/competitions/{competition_id}",
    response_model=CompetitionRead,
    summary="Get a canonical competition",
)
async def get_competition(competition_id: UUID, session: SessionDependency) -> CompetitionRead:
    """Fetch one non-deleted competition by its canonical UUID."""
    competition = _require(
        await CompetitionRepository(session).get(competition_id), "Competition", competition_id
    )
    return CompetitionRead.model_validate(competition)


@router.get("/seasons", response_model=Page[SeasonRead], summary="List canonical seasons")
async def list_seasons(
    filters: Annotated[SeasonFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[SeasonRead]:
    """List active seasons by competition and lifecycle status."""
    return _page(await SeasonRepository(session).list(filters, pagination), SeasonRead)


@router.get("/seasons/{season_id}", response_model=SeasonRead, summary="Get a canonical season")
async def get_season(season_id: UUID, session: SessionDependency) -> SeasonRead:
    """Fetch one non-deleted season by its canonical UUID."""
    season = _require(await SeasonRepository(session).get(season_id), "Season", season_id)
    return SeasonRead.model_validate(season)


@router.get("/teams", response_model=Page[TeamRead], summary="List canonical teams")
async def list_teams(
    filters: Annotated[TeamFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[TeamRead]:
    """List active teams by country, sport, team type, or name."""
    return _page(await TeamRepository(session).list(filters, pagination), TeamRead)


@router.get("/teams/{team_id}", response_model=TeamRead, summary="Get a canonical team")
async def get_team(team_id: UUID, session: SessionDependency) -> TeamRead:
    """Fetch one non-deleted team by its canonical UUID."""
    team = _require(await TeamRepository(session).get(team_id), "Team", team_id)
    return TeamRead.model_validate(team)


@router.get("/venues", response_model=Page[VenueRead], summary="List canonical venues")
async def list_venues(
    filters: Annotated[VenueFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[VenueRead]:
    """List active venues by country, timezone, or name."""
    return _page(await VenueRepository(session).list(filters, pagination), VenueRead)


@router.get("/venues/{venue_id}", response_model=VenueRead, summary="Get a canonical venue")
async def get_venue(venue_id: UUID, session: SessionDependency) -> VenueRead:
    """Fetch one non-deleted venue by its canonical UUID."""
    venue = _require(await VenueRepository(session).get(venue_id), "Venue", venue_id)
    return VenueRead.model_validate(venue)


@router.get("/timezones", response_model=Page[TimezoneRead], summary="List IANA timezones")
async def list_timezones(
    filters: Annotated[TimezoneFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[TimezoneRead]:
    """List canonical IANA timezones by name, active state, or primary country."""
    return _page(await TimezoneRepository(session).list(filters, pagination), TimezoneRead)


@router.get("/timezones/{timezone_id}", response_model=TimezoneRead, summary="Get an IANA timezone")
async def get_timezone(timezone_id: UUID, session: SessionDependency) -> TimezoneRead:
    """Fetch one timezone by its canonical UUID."""
    timezone = _require(await TimezoneRepository(session).get(timezone_id), "Timezone", timezone_id)
    return TimezoneRead.model_validate(timezone)


@router.get(
    "/fixture-statuses",
    response_model=Page[FixtureStatusRead],
    summary="List canonical fixture statuses",
)
async def list_fixture_statuses(
    pagination: PaginationDependency, session: SessionDependency
) -> Page[FixtureStatusRead]:
    """List the seeded, extensible fixture-status taxonomy."""
    return _page(await FixtureStatusRepository(session).list(pagination), FixtureStatusRead)


@router.get(
    "/fixture-statuses/{fixture_status_id}",
    response_model=FixtureStatusRead,
    summary="Get a canonical fixture status",
)
async def get_fixture_status(
    fixture_status_id: UUID, session: SessionDependency
) -> FixtureStatusRead:
    """Fetch one fixture status by its canonical UUID."""
    fixture_status = _require(
        await FixtureStatusRepository(session).get(fixture_status_id),
        "Fixture status",
        fixture_status_id,
    )
    return FixtureStatusRead.model_validate(fixture_status)


@router.get("/fixtures", response_model=Page[FixtureRead], summary="List canonical fixtures")
async def list_fixtures(
    filters: Annotated[FixtureFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[FixtureRead]:
    """List fixtures by season, competition, teams, status, venue, or time window."""
    return _page(await FixtureRepository(session).list(filters, pagination), FixtureRead)


@router.get("/fixtures/{fixture_id}", response_model=FixtureRead, summary="Get a canonical fixture")
async def get_fixture(fixture_id: UUID, session: SessionDependency) -> FixtureRead:
    """Fetch one immutable fixture record by its canonical UUID."""
    fixture = _require(await FixtureRepository(session).get(fixture_id), "Fixture", fixture_id)
    return FixtureRead.model_validate(fixture)


@router.get("/officials", response_model=Page[OfficialRead], summary="List canonical officials")
async def list_officials(
    filters: Annotated[OfficialFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
) -> Page[OfficialRead]:
    """List active officials by country or full name."""
    return _page(await OfficialRepository(session).list(filters, pagination), OfficialRead)


@router.get(
    "/officials/{official_id}", response_model=OfficialRead, summary="Get a canonical official"
)
async def get_official(official_id: UUID, session: SessionDependency) -> OfficialRead:
    """Fetch one non-deleted official by its canonical UUID."""
    official = _require(await OfficialRepository(session).get(official_id), "Official", official_id)
    return OfficialRead.model_validate(official)
