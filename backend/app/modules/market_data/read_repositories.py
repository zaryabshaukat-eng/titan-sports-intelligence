"""Read-only async repositories for Market Data history, latest views, and movement APIs."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.market_data.models import (
    Bookmaker,
    Market,
    MarketStatus,
    MarketType,
    OddsMovement,
    OddsSnapshot,
    Selection,
)
from app.modules.market_data.schemas import (
    BookmakerFilters,
    MarketFilters,
    OddsMovementFilters,
    OddsSnapshotFilters,
    PaginationParams,
)


@dataclass(frozen=True, slots=True)
class PageResult[EntityT]:
    """A database page independent of HTTP serialization."""

    items: list[EntityT]
    total: int
    limit: int
    offset: int


class ReadRepository:
    """Shared offset-pagination mechanics for Market Data read repositories."""

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


class BookmakerRepository(ReadRepository):
    """Query active canonical bookmakers without exposing soft-deleted source data."""

    async def list(
        self, filters: BookmakerFilters, pagination: PaginationParams
    ) -> PageResult[Bookmaker]:
        statement = select(Bookmaker).where(Bookmaker.deleted_at.is_(None))
        if filters.q:
            statement = statement.where(Bookmaker.name.ilike(f"%{filters.q}%"))
        if filters.is_active is not None:
            statement = statement.where(Bookmaker.is_active == filters.is_active)
        return await self._page(statement.order_by(Bookmaker.name), pagination)

    async def get(self, bookmaker_id: UUID) -> Bookmaker | None:
        """Load one active canonical bookmaker by UUID."""
        return await self._session.scalar(
            select(Bookmaker).where(Bookmaker.id == bookmaker_id, Bookmaker.deleted_at.is_(None))
        )


class MarketTypeRepository(ReadRepository):
    """Query extensible canonical market type taxonomy."""

    async def list(self, pagination: PaginationParams) -> PageResult[MarketType]:
        """List configured market types in stable code order."""
        return await self._page(select(MarketType).order_by(MarketType.code), pagination)


class MarketStatusRepository(ReadRepository):
    """Query the configured market status taxonomy."""

    async def list(self, pagination: PaginationParams) -> PageResult[MarketStatus]:
        """List market statuses in lifecycle sort order."""
        return await self._page(
            select(MarketStatus).order_by(MarketStatus.sort_order, MarketStatus.code), pagination
        )


class MarketRepository(ReadRepository):
    """Query fixture-scoped canonical markets and their durable selections."""

    async def list(
        self, filters: MarketFilters, pagination: PaginationParams
    ) -> PageResult[Market]:
        """List canonical markets with fixture, type, status, and period filters."""
        statement = select(Market)
        if filters.fixture_id:
            statement = statement.where(Market.fixture_id == filters.fixture_id)
        if filters.market_type_id:
            statement = statement.where(Market.market_type_id == filters.market_type_id)
        if filters.market_status_id:
            statement = statement.where(Market.market_status_id == filters.market_status_id)
        if filters.period_code:
            statement = statement.where(Market.period_code == filters.period_code.lower())
        return await self._page(
            statement.order_by(Market.fixture_id, Market.created_at.desc()), pagination
        )

    async def get(self, market_id: UUID) -> Market | None:
        """Load one canonical market by UUID."""
        return await self._session.get(Market, market_id)

    async def list_selections(
        self, market_id: UUID, pagination: PaginationParams
    ) -> PageResult[Selection]:
        """List both active and historically removed selections for historical replay."""
        statement = (
            select(Selection).where(Selection.market_id == market_id).order_by(Selection.name)
        )
        return await self._page(statement, pagination)


class OddsSnapshotRepository(ReadRepository):
    """Query immutable odds observations and derived latest-observation views."""

    async def list_history(
        self, filters: OddsSnapshotFilters, pagination: PaginationParams
    ) -> PageResult[OddsSnapshot]:
        """List raw immutable snapshots in chronological order with bounded filters."""
        statement = self._apply_filters(select(OddsSnapshot), filters).order_by(
            OddsSnapshot.observed_at.desc(), OddsSnapshot.created_at.desc()
        )
        return await self._page(statement, pagination)

    async def list_latest(
        self, filters: OddsSnapshotFilters, pagination: PaginationParams
    ) -> PageResult[OddsSnapshot]:
        """List the latest observed price per provider, bookmaker, and selection."""
        ranked = select(
            OddsSnapshot.id.label("snapshot_id"),
            func.row_number()
            .over(
                partition_by=(
                    OddsSnapshot.provider_name,
                    OddsSnapshot.bookmaker_id,
                    OddsSnapshot.selection_id,
                ),
                order_by=(OddsSnapshot.observed_at.desc(), OddsSnapshot.created_at.desc()),
            )
            .label("rank"),
        ).subquery()
        statement = select(OddsSnapshot).join(ranked, ranked.c.snapshot_id == OddsSnapshot.id)
        statement = (
            self._apply_filters(statement, filters)
            .where(ranked.c.rank == 1)
            .order_by(OddsSnapshot.observed_at.desc(), OddsSnapshot.created_at.desc())
        )
        return await self._page(statement, pagination)

    @staticmethod
    def _apply_filters(
        statement: Select[tuple[OddsSnapshot]], filters: OddsSnapshotFilters
    ) -> Select[tuple[OddsSnapshot]]:
        """Apply all immutable snapshot filters consistently to history and latest views."""
        if filters.provider_name:
            statement = statement.where(OddsSnapshot.provider_name == filters.provider_name.lower())
        if filters.bookmaker_id:
            statement = statement.where(OddsSnapshot.bookmaker_id == filters.bookmaker_id)
        if filters.fixture_id:
            statement = statement.where(OddsSnapshot.fixture_id == filters.fixture_id)
        if filters.market_id:
            statement = statement.where(OddsSnapshot.market_id == filters.market_id)
        if filters.selection_id:
            statement = statement.where(OddsSnapshot.selection_id == filters.selection_id)
        if filters.observed_after:
            statement = statement.where(OddsSnapshot.observed_at >= filters.observed_after)
        if filters.observed_before:
            statement = statement.where(OddsSnapshot.observed_at <= filters.observed_before)
        return statement


class OddsMovementRepository(ReadRepository):
    """Query append-only price, market status, and selection lifecycle movement records."""

    async def list(
        self, filters: OddsMovementFilters, pagination: PaginationParams
    ) -> PageResult[OddsMovement]:
        """List movement history with fixture, market, selection, bookmaker, and time filters."""
        statement = select(OddsMovement)
        if filters.fixture_id:
            statement = statement.join(Market, Market.id == OddsMovement.market_id).where(
                Market.fixture_id == filters.fixture_id
            )
        if filters.bookmaker_id:
            statement = statement.where(OddsMovement.bookmaker_id == filters.bookmaker_id)
        if filters.market_id:
            statement = statement.where(OddsMovement.market_id == filters.market_id)
        if filters.selection_id:
            statement = statement.where(OddsMovement.selection_id == filters.selection_id)
        if filters.movement_type:
            statement = statement.where(OddsMovement.movement_type == filters.movement_type)
        if filters.observed_after:
            statement = statement.where(OddsMovement.observed_at >= filters.observed_after)
        if filters.observed_before:
            statement = statement.where(OddsMovement.observed_at <= filters.observed_before)
        return await self._page(
            statement.order_by(OddsMovement.observed_at.desc(), OddsMovement.created_at.desc()),
            pagination,
        )
