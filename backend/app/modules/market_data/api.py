"""Protected internal API adapters for Market Data ingestion and read-only history queries."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require_authenticated_principal
from app.modules.market_data.exceptions import UnknownOddsProviderError
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
    BookmakerRead,
    MarketFilters,
    MarketRead,
    MarketStatusRead,
    MarketTypeRead,
    OddsIngestionBatchResult,
    OddsIngestionRequest,
    OddsMovementFilters,
    OddsMovementRead,
    OddsSnapshotFilters,
    OddsSnapshotRead,
    Page,
    PaginationParams,
    SelectionRead,
)
from app.modules.market_data.service import OddsIngestionService
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/market-data", tags=["Market Data"])

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
PrincipalDependency = Annotated[Principal, Depends(require_authenticated_principal)]
PaginationDependency = Annotated[PaginationParams, Depends()]


def _page[SchemaT: BaseModel](result: PageResult[object], schema: type[SchemaT]) -> Page[SchemaT]:
    """Convert repository entities to documented internal read-only response contracts."""
    return Page[SchemaT](
        items=[schema.model_validate(item) for item in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


def _require[EntityT](entity: EntityT | None, resource_name: str, resource_id: UUID) -> EntityT:
    """Return one entity or emit the consistent internal resource-not-found response."""
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "market_data_resource_not_found",
                "message": f"{resource_name} '{resource_id}' was not found.",
            },
        )
    return entity


@router.post(
    "/ingestion/odds/{provider_name}",
    response_model=OddsIngestionBatchResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest an odds-provider batch",
    description=(
        "Protected internal endpoint. It retains source JSON, appends immutable snapshots, "
        "detects movements, and records audit and transactional-outbox evidence."
    ),
)
async def ingest_odds_batch(
    provider_name: str,
    request_body: OddsIngestionRequest,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> OddsIngestionBatchResult:
    """Run one registered odds-provider adapter inside the request-scoped transaction."""
    _ = principal
    registry: OddsProviderRegistry = request.app.state.odds_provider_registry
    try:
        adapter = registry.get(provider_name)
    except UnknownOddsProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "market_data_provider_not_found",
                "message": f"Odds provider '{provider_name}' is not registered.",
            },
        ) from exc
    return await OddsIngestionService(session=session, provider_adapter=adapter).ingest(
        request_body.payloads
    )


@router.get("/bookmakers", response_model=Page[BookmakerRead], summary="List bookmakers")
async def list_bookmakers(
    filters: Annotated[BookmakerFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[BookmakerRead]:
    """List canonical active bookmaker identities for internal market operations."""
    _ = principal
    return _page(await BookmakerRepository(session).list(filters, pagination), BookmakerRead)


@router.get("/bookmakers/{bookmaker_id}", response_model=BookmakerRead, summary="Get a bookmaker")
async def get_bookmaker(
    bookmaker_id: UUID, session: SessionDependency, principal: PrincipalDependency
) -> BookmakerRead:
    """Fetch one active canonical bookmaker."""
    _ = principal
    bookmaker = _require(
        await BookmakerRepository(session).get(bookmaker_id), "Bookmaker", bookmaker_id
    )
    return BookmakerRead.model_validate(bookmaker)


@router.get("/market-types", response_model=Page[MarketTypeRead], summary="List market types")
async def list_market_types(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[MarketTypeRead]:
    """List extensible canonical market type definitions."""
    _ = principal
    return _page(await MarketTypeRepository(session).list(pagination), MarketTypeRead)


@router.get(
    "/market-statuses", response_model=Page[MarketStatusRead], summary="List market statuses"
)
async def list_market_statuses(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[MarketStatusRead]:
    """List configured canonical market lifecycle statuses."""
    _ = principal
    return _page(await MarketStatusRepository(session).list(pagination), MarketStatusRead)


@router.get("/markets", response_model=Page[MarketRead], summary="List fixture markets")
async def list_markets(
    filters: Annotated[MarketFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[MarketRead]:
    """List canonical fixture markets with filterable type, status, period, and fixture scope."""
    _ = principal
    return _page(await MarketRepository(session).list(filters, pagination), MarketRead)


@router.get("/markets/{market_id}", response_model=MarketRead, summary="Get a fixture market")
async def get_market(
    market_id: UUID, session: SessionDependency, principal: PrincipalDependency
) -> MarketRead:
    """Fetch one canonical market by UUID."""
    _ = principal
    market = _require(await MarketRepository(session).get(market_id), "Market", market_id)
    return MarketRead.model_validate(market)


@router.get(
    "/markets/{market_id}/selections",
    response_model=Page[SelectionRead],
    summary="List market selections",
)
async def list_market_selections(
    market_id: UUID,
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[SelectionRead]:
    """List active and removed selections, preserving the complete historical market structure."""
    _ = principal
    _require(await MarketRepository(session).get(market_id), "Market", market_id)
    return _page(
        await MarketRepository(session).list_selections(market_id, pagination), SelectionRead
    )


@router.get(
    "/odds-snapshots",
    response_model=Page[OddsSnapshotRead],
    summary="List immutable odds snapshots",
)
async def list_odds_snapshots(
    filters: Annotated[OddsSnapshotFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[OddsSnapshotRead]:
    """List immutable price observations for audit, replay, and historical analysis."""
    _ = principal
    return _page(
        await OddsSnapshotRepository(session).list_history(filters, pagination), OddsSnapshotRead
    )


@router.get("/odds-history", response_model=Page[OddsSnapshotRead], summary="Query odds history")
async def query_odds_history(
    filters: Annotated[OddsSnapshotFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[OddsSnapshotRead]:
    """Query chronological immutable odds history using the same filter contract as snapshots."""
    _ = principal
    return _page(
        await OddsSnapshotRepository(session).list_history(filters, pagination), OddsSnapshotRead
    )


@router.get("/latest-odds", response_model=Page[OddsSnapshotRead], summary="List latest odds")
async def list_latest_odds(
    filters: Annotated[OddsSnapshotFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[OddsSnapshotRead]:
    """List the latest observed price for each provider-bookmaker-selection combination."""
    _ = principal
    return _page(
        await OddsSnapshotRepository(session).list_latest(filters, pagination), OddsSnapshotRead
    )


@router.get(
    "/fixtures/{fixture_id}/odds",
    response_model=Page[OddsSnapshotRead],
    summary="List fixture odds history",
)
async def list_fixture_odds(
    fixture_id: UUID,
    filters: Annotated[OddsSnapshotFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[OddsSnapshotRead]:
    """List immutable odds snapshots scoped to one canonical fixture."""
    _ = principal
    filters.fixture_id = fixture_id
    return _page(
        await OddsSnapshotRepository(session).list_history(filters, pagination), OddsSnapshotRead
    )


@router.get(
    "/fixtures/{fixture_id}/markets/{market_id}/odds",
    response_model=Page[OddsSnapshotRead],
    summary="List fixture market odds history",
)
async def list_fixture_market_odds(
    fixture_id: UUID,
    market_id: UUID,
    filters: Annotated[OddsSnapshotFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[OddsSnapshotRead]:
    """List immutable snapshots for one market only when it belongs to the requested fixture."""
    _ = principal
    filters.fixture_id = fixture_id
    filters.market_id = market_id
    return _page(
        await OddsSnapshotRepository(session).list_history(filters, pagination), OddsSnapshotRead
    )


@router.get(
    "/movement-history",
    response_model=Page[OddsMovementRead],
    summary="List market movement history",
)
async def list_movement_history(
    filters: Annotated[OddsMovementFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[OddsMovementRead]:
    """List append-only opening, closing, price, status, and selection lifecycle movements."""
    _ = principal
    return _page(await OddsMovementRepository(session).list(filters, pagination), OddsMovementRead)
