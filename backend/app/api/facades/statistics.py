"""Thin API facade for Statistics ingestion and immutable read queries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.statistics.models import StatisticCategory, StatisticSnapshot
from app.modules.statistics.providers.registry import StatisticsProviderRegistry
from app.modules.statistics.schemas import Pagination, StatisticsIngestionResult
from app.modules.statistics.service import StatisticsIngestionService


class StatisticsApiFacade:
    """Delegate Statistics API work to the established service and persistence layer."""

    def __init__(
        self, session: AsyncSession, registry: StatisticsProviderRegistry | None = None
    ) -> None:
        self._session = session
        self._registry = registry

    async def ingest(
        self, provider_name: str, payloads: list[dict[str, object]]
    ) -> StatisticsIngestionResult:
        """Delegate ingestion to the existing transactional service."""
        if self._registry is None:
            raise RuntimeError("A statistics provider registry is required for ingestion.")
        return await StatisticsIngestionService(
            self._session, self._registry.get(provider_name)
        ).ingest(payloads)

    async def categories(self, pagination: Pagination) -> tuple[list[object], int]:
        """Return the existing stable, paginated category read model."""
        total = await self._session.scalar(select(func.count()).select_from(StatisticCategory)) or 0
        rows = list(
            (
                await self._session.scalars(
                    select(StatisticCategory)
                    .order_by(StatisticCategory.code)
                    .offset(pagination.offset)
                    .limit(pagination.limit)
                )
            ).all()
        )
        return rows, total

    async def snapshots(
        self,
        fixture_id: UUID | None,
        scope: str | None,
        pagination: Pagination,
        *,
        latest_only: bool = False,
    ) -> tuple[list[object], int]:
        """Return the legacy history/latest query result without changing its semantics."""
        statement = select(StatisticSnapshot)
        if latest_only:
            ranked = select(
                StatisticSnapshot.id.label("snapshot_id"),
                func.row_number()
                .over(
                    partition_by=StatisticSnapshot.series_id,
                    order_by=(
                        StatisticSnapshot.observed_at.desc(),
                        StatisticSnapshot.created_at.desc(),
                    ),
                )
                .label("rank"),
            ).subquery()
            statement = statement.join(ranked, ranked.c.snapshot_id == StatisticSnapshot.id).where(
                ranked.c.rank == 1
            )
        if fixture_id:
            statement = statement.where(StatisticSnapshot.fixture_id == fixture_id)
        if scope:
            statement = statement.where(StatisticSnapshot.scope == scope)
        count = select(func.count()).select_from(statement.order_by(None).subquery())
        total = await self._session.scalar(count) or 0
        rows = list(
            (
                await self._session.scalars(
                    statement.order_by(StatisticSnapshot.observed_at.desc())
                    .offset(pagination.offset)
                    .limit(pagination.limit)
                )
            ).all()
        )
        return rows, total
