"""Async persistence helpers; append-only snapshot creation is centralized here."""

# ruff: noqa: E501, E701, E702
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.models import FixtureProviderIdentity
from app.modules.sports.models import Team
from app.modules.statistics.enums import StatisticMappingEntityType, StatisticScope
from app.modules.statistics.exceptions import StatisticsResolutionError
from app.modules.statistics.models import (
    FixtureStatistic,
    PlayerStatistic,
    StatisticCategory,
    StatisticPlayer,
    StatisticProvider,
    StatisticProviderMapping,
    StatisticVersion,
    TeamStatistic,
)
from app.modules.statistics.schemas import CategoryInput, NormalizedStatistic


class StatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def provider(self, name: str) -> StatisticProvider:
        item = await self.session.scalar(
            select(StatisticProvider).where(StatisticProvider.name == name)
        )
        if item is None:
            item = StatisticProvider(name=name, display_name=name.replace("_", " ").title())
            self.session.add(item)
            await self.session.flush()
        return item

    async def fixture(self, provider_name: str, provider_id: str) -> UUID | None:
        return await self.session.scalar(
            select(FixtureProviderIdentity.fixture_id).where(
                FixtureProviderIdentity.provider_name == provider_name,
                FixtureProviderIdentity.provider_fixture_id == provider_id,
            )
        )

    async def category(
        self, provider: StatisticProvider, source: CategoryInput
    ) -> StatisticCategory:
        mapping = await self.session.scalar(
            select(StatisticProviderMapping).where(
                StatisticProviderMapping.provider_id == provider.id,
                StatisticProviderMapping.entity_type == StatisticMappingEntityType.CATEGORY,
                StatisticProviderMapping.provider_entity_id == source.code,
            )
        )
        item = (
            await self.session.get(StatisticCategory, mapping.canonical_entity_id)
            if mapping
            else None
        )
        if item is None:
            item = await self.session.scalar(
                select(StatisticCategory).where(StatisticCategory.code == source.code)
            )
        if item is None:
            item = StatisticCategory(
                code=source.code, name=source.name, value_schema=source.value_schema
            )
            self.session.add(item)
            await self.session.flush()
        if mapping is None:
            self.session.add(
                StatisticProviderMapping(
                    provider_id=provider.id,
                    entity_type=StatisticMappingEntityType.CATEGORY,
                    provider_entity_id=source.code,
                    canonical_entity_id=item.id,
                )
            )
        return item

    async def version(
        self, provider: StatisticProvider, category: StatisticCategory, value: str
    ) -> StatisticVersion:
        item = await self.session.scalar(
            select(StatisticVersion).where(
                StatisticVersion.provider_id == provider.id,
                StatisticVersion.category_id == category.id,
                StatisticVersion.version == value,
            )
        )
        if item is None:
            item = StatisticVersion(
                provider_id=provider.id,
                category_id=category.id,
                version=value,
                schema=category.value_schema,
            )
            self.session.add(item)
            await self.session.flush()
        return item

    async def team(self, provider: StatisticProvider, source_id: str, name: str) -> Team:
        mapping = await self.session.scalar(
            select(StatisticProviderMapping).where(
                StatisticProviderMapping.provider_id == provider.id,
                StatisticProviderMapping.entity_type == StatisticMappingEntityType.TEAM,
                StatisticProviderMapping.provider_entity_id == source_id,
            )
        )
        item = await self.session.get(Team, mapping.canonical_entity_id) if mapping else None
        if item is None:
            item = await self.session.scalar(
                select(Team).where(Team.name == name, Team.deleted_at.is_(None))
            )
        if item is None:
            raise StatisticsResolutionError(f"Canonical team '{name}' is not available.")
        if mapping is None:
            self.session.add(
                StatisticProviderMapping(
                    provider_id=provider.id,
                    entity_type=StatisticMappingEntityType.TEAM,
                    provider_entity_id=source_id,
                    canonical_entity_id=item.id,
                )
            )
        return item

    async def player(
        self, provider: StatisticProvider, source_id: str, name: str, birth_date: str | None
    ) -> StatisticPlayer:
        mapping = await self.session.scalar(
            select(StatisticProviderMapping).where(
                StatisticProviderMapping.provider_id == provider.id,
                StatisticProviderMapping.entity_type == StatisticMappingEntityType.PLAYER,
                StatisticProviderMapping.provider_entity_id == source_id,
            )
        )
        item = (
            await self.session.get(StatisticPlayer, mapping.canonical_entity_id)
            if mapping
            else None
        )
        if item is None:
            item = await self.session.scalar(
                select(StatisticPlayer).where(
                    StatisticPlayer.name == name, StatisticPlayer.birth_date == birth_date
                )
            )
        if item is None:
            item = StatisticPlayer(name=name, birth_date=birth_date)
            self.session.add(item)
            await self.session.flush()
        if mapping is None:
            self.session.add(
                StatisticProviderMapping(
                    provider_id=provider.id,
                    entity_type=StatisticMappingEntityType.PLAYER,
                    provider_entity_id=source_id,
                    canonical_entity_id=item.id,
                )
            )
        return item

    async def series(
        self, fixture_id: UUID, provider: StatisticProvider, statistic: NormalizedStatistic
    ) -> tuple[UUID, dict[str, UUID | None]]:
        category = await self.category(provider, statistic.category)
        version = await self.version(provider, category, statistic.version)
        refs: dict[str, UUID | None] = {
            "fixture_statistic_id": None,
            "team_statistic_id": None,
            "player_statistic_id": None,
        }
        if statistic.scope is StatisticScope.FIXTURE:
            row = await self.session.scalar(
                select(FixtureStatistic).where(
                    FixtureStatistic.fixture_id == fixture_id,
                    FixtureStatistic.category_id == category.id,
                    FixtureStatistic.version_id == version.id,
                )
            )
            if row is None:
                row = FixtureStatistic(
                    fixture_id=fixture_id, category_id=category.id, version_id=version.id
                )
                self.session.add(row)
                await self.session.flush()
            refs["fixture_statistic_id"] = row.id
            return row.id, refs
        if statistic.scope is StatisticScope.TEAM:
            if statistic.team is None:
                raise StatisticsResolutionError("A team statistic requires a team reference.")
            team = await self.team(provider, statistic.team.id, statistic.team.name)
            row = await self.session.scalar(
                select(TeamStatistic).where(
                    TeamStatistic.fixture_id == fixture_id,
                    TeamStatistic.team_id == team.id,
                    TeamStatistic.category_id == category.id,
                    TeamStatistic.version_id == version.id,
                )
            )
            if row is None:
                row = TeamStatistic(
                    fixture_id=fixture_id,
                    team_id=team.id,
                    category_id=category.id,
                    version_id=version.id,
                )
                self.session.add(row)
                await self.session.flush()
            refs["team_statistic_id"] = row.id
            return row.id, refs
        if statistic.player is None:
            raise StatisticsResolutionError("A player statistic requires a player reference.")
        player = await self.player(
            provider, statistic.player.id, statistic.player.name, statistic.player.birth_date
        )
        team_id = (
            (await self.team(provider, statistic.team.id, statistic.team.name)).id
            if statistic.team
            else None
        )
        row = await self.session.scalar(
            select(PlayerStatistic).where(
                PlayerStatistic.fixture_id == fixture_id,
                PlayerStatistic.player_id == player.id,
                PlayerStatistic.category_id == category.id,
                PlayerStatistic.version_id == version.id,
            )
        )
        if row is None:
            row = PlayerStatistic(
                fixture_id=fixture_id,
                player_id=player.id,
                team_id=team_id,
                category_id=category.id,
                version_id=version.id,
            )
            self.session.add(row)
            await self.session.flush()
        refs["player_statistic_id"] = row.id
        return row.id, refs
