"""Provider-neutral resolution from normalized DTOs to canonical Sports entities."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.enums import ProviderEntityType
from app.modules.ingestion.exceptions import PayloadValidationError
from app.modules.ingestion.repositories import IngestionRepository
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
from app.modules.sports.models import (
    Competition,
    Country,
    FixtureStatus,
    League,
    Official,
    Season,
    Team,
    Timezone,
    Venue,
)


@dataclass(frozen=True, slots=True)
class ResolvedFixtureReferences:
    """Canonical UUIDs required to create or safely update one fixture."""

    country_id: UUID
    league_id: UUID
    competition_id: UUID
    season_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    fixture_status_id: UUID
    timezone_id: UUID
    venue_id: UUID | None


class CanonicalEntityResolver:
    """Resolve external identities without adding provider fields to Sports Domain tables."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        ingestion_repository: IngestionRepository,
        provider_name: str,
    ) -> None:
        self.session = session
        self.ingestion_repository = ingestion_repository
        self.provider_name = provider_name

    async def resolve(self, fixture: NormalizedFixture) -> ResolvedFixtureReferences:
        """Resolve all canonical dependencies in foreign-key-safe order."""
        country = await self.resolve_country(fixture.country)
        timezone = await self.resolve_timezone(fixture.timezone_iana_name)
        league = await self.resolve_league(fixture.league, fixture.sport, country.id)
        competition = await self.resolve_competition(
            fixture.competition, fixture.sport, league.id, country.id, timezone.id
        )
        season = await self.resolve_season(fixture.season, competition.id)
        home_team = await self.resolve_team(fixture.home_team, fixture.sport)
        away_team = await self.resolve_team(fixture.away_team, fixture.sport)
        venue = (
            await self.resolve_venue(fixture.venue, timezone.id)
            if fixture.venue is not None
            else None
        )
        fixture_status = await self.resolve_fixture_status(fixture.fixture_status_code)

        return ResolvedFixtureReferences(
            country_id=country.id,
            league_id=league.id,
            competition_id=competition.id,
            season_id=season.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            fixture_status_id=fixture_status.id,
            timezone_id=timezone.id,
            venue_id=venue.id if venue is not None else None,
        )

    async def resolve_country(self, value: NormalizedCountry) -> Country:
        """Resolve by stable provider ID, then immutable ISO natural key, then create."""
        mapped = await self._mapped_entity(ProviderEntityType.COUNTRY, value.provider_id, Country)
        if mapped is not None:
            return mapped

        country = await self.session.scalar(
            select(Country).where(Country.iso_code == value.iso_code)
        )
        if country is None:
            country = Country(name=value.name, iso_code=value.iso_code, iso3_code=value.iso3_code)
            self.session.add(country)
            await self.session.flush()
        await self._link(ProviderEntityType.COUNTRY, value.provider_id, country.id)
        return country

    async def resolve_timezone(self, iana_name: str) -> Timezone:
        """Resolve IANA timezone by its canonical natural key or create reference data."""
        timezone = await self.session.scalar(
            select(Timezone).where(Timezone.iana_name == iana_name)
        )
        if timezone is None:
            timezone = Timezone(iana_name=iana_name, display_name=iana_name)
            self.session.add(timezone)
            await self.session.flush()
        return timezone

    async def resolve_league(self, value: NormalizedLeague, sport: str, country_id: UUID) -> League:
        """Resolve a league using provider identity or canonical country/sport/name uniqueness."""
        mapped = await self._mapped_entity(ProviderEntityType.LEAGUE, value.provider_id, League)
        if mapped is not None:
            return mapped

        league = await self.session.scalar(
            select(League).where(
                League.country_id == country_id,
                League.sport == sport,
                func.lower(League.name) == value.name.lower(),
            )
        )
        if league is None:
            league = League(
                name=value.name,
                short_name=value.short_name,
                sport=sport,
                country_id=country_id,
            )
            self.session.add(league)
            await self.session.flush()
        await self._link(ProviderEntityType.LEAGUE, value.provider_id, league.id)
        return league

    async def resolve_competition(
        self,
        value: NormalizedCompetition,
        sport: str,
        league_id: UUID,
        country_id: UUID,
        timezone_id: UUID,
    ) -> Competition:
        """Resolve a competition under its canonical owning league."""
        mapped = await self._mapped_entity(
            ProviderEntityType.COMPETITION, value.provider_id, Competition
        )
        if mapped is not None:
            return mapped

        competition = await self.session.scalar(
            select(Competition).where(
                Competition.league_id == league_id,
                func.lower(Competition.name) == value.name.lower(),
            )
        )
        if competition is None:
            competition = Competition(
                name=value.name,
                short_name=value.short_name,
                sport=sport,
                competition_type=value.competition_type,
                league_id=league_id,
                country_id=country_id,
                default_timezone_id=timezone_id,
            )
            self.session.add(competition)
            await self.session.flush()
        await self._link(ProviderEntityType.COMPETITION, value.provider_id, competition.id)
        return competition

    async def resolve_season(self, value: NormalizedSeason, competition_id: UUID) -> Season:
        """Resolve a season under its canonical competition."""
        mapped = await self._mapped_entity(ProviderEntityType.SEASON, value.provider_id, Season)
        if mapped is not None:
            return mapped

        season = await self.session.scalar(
            select(Season).where(
                Season.competition_id == competition_id,
                func.lower(Season.name) == value.name.lower(),
            )
        )
        if season is None:
            season = Season(
                competition_id=competition_id,
                name=value.name,
                start_date=value.start_date,
                end_date=value.end_date,
                status=value.status,
            )
            self.session.add(season)
            await self.session.flush()
        await self._link(ProviderEntityType.SEASON, value.provider_id, season.id)
        return season

    async def resolve_team(self, value: NormalizedTeam, sport: str) -> Team:
        """Resolve a team by external identity, then conservative country/sport/name matching."""
        mapped = await self._mapped_entity(ProviderEntityType.TEAM, value.provider_id, Team)
        if mapped is not None:
            return mapped

        country_id = await self._country_id_for_iso(value.country_iso_code)
        country_predicate = (
            Team.country_id == country_id if country_id is not None else Team.country_id.is_(None)
        )
        team = await self.session.scalar(
            select(Team).where(
                country_predicate,
                Team.sport == sport,
                func.lower(Team.name) == value.name.lower(),
            )
        )
        if team is None:
            team = Team(
                name=value.name,
                short_name=value.short_name,
                sport=sport,
                team_type=value.team_type,
                founded_year=value.founded_year,
                country_id=country_id,
            )
            self.session.add(team)
            await self.session.flush()
        await self._link(ProviderEntityType.TEAM, value.provider_id, team.id)
        return team

    async def resolve_venue(self, value: NormalizedVenue, fixture_timezone_id: UUID) -> Venue:
        """Resolve venue identity; venue data is optional and does not fabricate countries."""
        mapped = await self._mapped_entity(ProviderEntityType.VENUE, value.provider_id, Venue)
        if mapped is not None:
            return mapped

        country_id = await self._country_id_for_iso(value.country_iso_code)
        timezone_id = (
            (await self.resolve_timezone(value.timezone_iana_name)).id
            if value.timezone_iana_name is not None
            else fixture_timezone_id
        )
        country_predicate = (
            Venue.country_id == country_id if country_id is not None else Venue.country_id.is_(None)
        )
        venue = await self.session.scalar(
            select(Venue).where(country_predicate, func.lower(Venue.name) == value.name.lower())
        )
        if venue is None:
            venue = Venue(
                name=value.name,
                city=value.city,
                address=value.address,
                capacity=value.capacity,
                country_id=country_id,
                timezone_id=timezone_id,
            )
            self.session.add(venue)
            await self.session.flush()
        await self._link(ProviderEntityType.VENUE, value.provider_id, venue.id)
        return venue

    async def resolve_official(self, value: NormalizedOfficial) -> Official:
        """Resolve an official using its provider identity; no unsafe name-only merge is used."""
        mapped = await self._mapped_entity(ProviderEntityType.OFFICIAL, value.provider_id, Official)
        if mapped is not None:
            return mapped

        official = Official(
            full_name=value.name,
            country_id=await self._country_id_for_iso(value.country_iso_code),
        )
        self.session.add(official)
        await self.session.flush()
        await self._link(ProviderEntityType.OFFICIAL, value.provider_id, official.id)
        return official

    async def resolve_fixture_status(self, code: str) -> FixtureStatus:
        """Resolve only seeded canonical status taxonomy; unknown states are validation failures."""
        fixture_status = await self.session.scalar(
            select(FixtureStatus).where(FixtureStatus.code == code)
        )
        if fixture_status is None:
            raise PayloadValidationError(
                [
                    {
                        "path": "fixture.status",
                        "message": f"canonical fixture status '{code}' is not configured",
                        "type": "unknown_canonical_status",
                    }
                ]
            )
        return fixture_status

    async def _country_id_for_iso(self, iso_code: str | None) -> UUID | None:
        """Resolve optional country references without guessing absent master data."""
        if iso_code is None:
            return None
        country = await self.session.scalar(select(Country).where(Country.iso_code == iso_code))
        return country.id if country is not None else None

    async def _mapped_entity[EntityT](
        self,
        entity_type: ProviderEntityType,
        provider_entity_id: str,
        entity_class: type[EntityT],
    ) -> EntityT | None:
        """Return a valid mapped canonical entity, never a type-unsafe UUID alone."""
        identity = await self.ingestion_repository.get_provider_entity_identity(
            self.provider_name, entity_type, provider_entity_id
        )
        if identity is None:
            return None
        entity = await self.session.get(entity_class, identity.canonical_entity_id)
        if entity is None:
            raise PayloadValidationError(
                [
                    {
                        "path": "entity_resolution",
                        "message": (
                            f"provider identity '{provider_entity_id}' points to a missing "
                            f"canonical {entity_type.value}"
                        ),
                        "type": "broken_provider_identity",
                    }
                ]
            )
        return entity

    async def _link(
        self, entity_type: ProviderEntityType, provider_entity_id: str, canonical_entity_id: UUID
    ) -> None:
        """Create an identity map after canonical resolution without provider fields in Sports."""
        await self.ingestion_repository.link_provider_entity(
            provider_name=self.provider_name,
            entity_type=entity_type,
            provider_entity_id=provider_entity_id,
            canonical_entity_id=canonical_entity_id,
        )
