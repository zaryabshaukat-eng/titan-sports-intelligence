"""Thin API facade for immutable Market Data ingestion and read queries."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.market_data.providers.base import OddsProviderAdapter
from app.modules.market_data.providers.registry import OddsProviderRegistry
from app.modules.market_data.read_repositories import (
    BookmakerRepository,
    MarketRepository,
    MarketStatusRepository,
    MarketTypeRepository,
    OddsMovementRepository,
    OddsSnapshotRepository,
    PageResult,
)
from app.modules.market_data.schemas import (
    BookmakerFilters,
    MarketFilters,
    OddsIngestionBatchResult,
    OddsMovementFilters,
    OddsSnapshotFilters,
    PaginationParams,
)
from app.modules.market_data.service import OddsIngestionService


class MarketDataApiFacade:
    """Delegate API operations to the existing Market Data application interfaces."""

    def __init__(self, session: AsyncSession, registry: OddsProviderRegistry | None = None) -> None:
        self._session = session
        self._registry = registry

    async def ingest(
        self, provider_name: str, payloads: list[dict[str, Any]]
    ) -> OddsIngestionBatchResult:
        """Delegate one provider batch without changing ingestion behavior."""
        if self._registry is None:
            raise RuntimeError("An odds provider registry is required for ingestion.")
        adapter: OddsProviderAdapter = self._registry.get(provider_name)
        return await OddsIngestionService(session=self._session, provider_adapter=adapter).ingest(
            payloads
        )

    async def list_bookmakers(
        self, filters: BookmakerFilters, pagination: PaginationParams
    ) -> PageResult[object]:
        return await BookmakerRepository(self._session).list(filters, pagination)

    async def get_bookmaker(self, bookmaker_id: UUID) -> object | None:
        return await BookmakerRepository(self._session).get(bookmaker_id)

    async def list_market_types(self, pagination: PaginationParams) -> PageResult[object]:
        return await MarketTypeRepository(self._session).list(pagination)

    async def list_market_statuses(self, pagination: PaginationParams) -> PageResult[object]:
        return await MarketStatusRepository(self._session).list(pagination)

    async def list_markets(
        self, filters: MarketFilters, pagination: PaginationParams
    ) -> PageResult[object]:
        return await MarketRepository(self._session).list(filters, pagination)

    async def get_market(self, market_id: UUID) -> object | None:
        return await MarketRepository(self._session).get(market_id)

    async def list_market_selections(
        self, market_id: UUID, pagination: PaginationParams
    ) -> PageResult[object]:
        return await MarketRepository(self._session).list_selections(market_id, pagination)

    async def list_odds_history(
        self, filters: OddsSnapshotFilters, pagination: PaginationParams
    ) -> PageResult[object]:
        return await OddsSnapshotRepository(self._session).list_history(filters, pagination)

    async def list_latest_odds(
        self, filters: OddsSnapshotFilters, pagination: PaginationParams
    ) -> PageResult[object]:
        return await OddsSnapshotRepository(self._session).list_latest(filters, pagination)

    async def list_movements(
        self, filters: OddsMovementFilters, pagination: PaginationParams
    ) -> PageResult[object]:
        return await OddsMovementRepository(self._session).list(filters, pagination)
