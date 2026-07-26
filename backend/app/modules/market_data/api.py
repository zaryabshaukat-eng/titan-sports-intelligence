"""Protected internal API adapters for Market Data ingestion and read-only history queries."""

from __future__ import annotations

from typing import Annotated, Protocol
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.market_data import MarketDataApiFacade
from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.market_data.exceptions import UnknownOddsProviderError
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
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/market-data", tags=["Market Data"])

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
PrincipalDependency = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipalDependency = Annotated[
    Principal, Depends(require_permissions(Permission.MARKET_DATA_INGEST))
]
PaginationDependency = Annotated[PaginationParams, Depends()]


def get_market_data_ingestion_facade(
    request: Request, session: SessionDependency
) -> MarketDataApiFacade:
    """Compose the write facade without exposing the provider registry to route handlers."""
    return MarketDataApiFacade(session, request.app.state.odds_provider_registry)


IngestionFacade = Annotated[MarketDataApiFacade, Depends(get_market_data_ingestion_facade)]


class PageResultContract(Protocol):
    """The facade-owned pagination result shape consumed by the transport adapter."""

    items: list[object]
    total: int
    limit: int
    offset: int


def _page[SchemaT: BaseModel](result: PageResultContract, schema: type[SchemaT]) -> Page[SchemaT]:
    """Convert facade entities to documented internal read-only response contracts."""
    return Page(
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
    facade: IngestionFacade,
    principal: WritePrincipalDependency,
) -> OddsIngestionBatchResult:
    """Run one registered odds-provider adapter inside the request-scoped transaction."""
    _ = principal
    try:
        result = await facade.ingest(provider_name, request_body.payloads)
    except UnknownOddsProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "market_data_provider_not_found",
                "message": f"Odds provider '{provider_name}' is not registered.",
            },
        ) from exc
    metrics = request.app.state.metrics
    if metrics is not None:
        failures = sum(item.outcome.value == "validation_failed" for item in result.items)
        metrics.observe_ingestion("market_data", provider_name, len(result.items), failures)
    return result


@router.get("/bookmakers", response_model=Page[BookmakerRead], summary="List bookmakers")
async def list_bookmakers(
    filters: Annotated[BookmakerFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[BookmakerRead]:
    """List canonical active bookmaker identities for internal market operations."""
    _ = principal
    return _page(
        await MarketDataApiFacade(session).list_bookmakers(filters, pagination), BookmakerRead
    )


@router.get("/bookmakers/{bookmaker_id}", response_model=BookmakerRead, summary="Get a bookmaker")
async def get_bookmaker(
    bookmaker_id: UUID, session: SessionDependency, principal: PrincipalDependency
) -> BookmakerRead:
    """Fetch one active canonical bookmaker."""
    _ = principal
    bookmaker = _require(
        await MarketDataApiFacade(session).get_bookmaker(bookmaker_id), "Bookmaker", bookmaker_id
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
    return _page(await MarketDataApiFacade(session).list_market_types(pagination), MarketTypeRead)


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
    return _page(
        await MarketDataApiFacade(session).list_market_statuses(pagination), MarketStatusRead
    )


@router.get("/markets", response_model=Page[MarketRead], summary="List fixture markets")
async def list_markets(
    filters: Annotated[MarketFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> Page[MarketRead]:
    """List canonical fixture markets with filterable type, status, period, and fixture scope."""
    _ = principal
    return _page(await MarketDataApiFacade(session).list_markets(filters, pagination), MarketRead)


@router.get("/markets/{market_id}", response_model=MarketRead, summary="Get a fixture market")
async def get_market(
    market_id: UUID, session: SessionDependency, principal: PrincipalDependency
) -> MarketRead:
    """Fetch one canonical market by UUID."""
    _ = principal
    market = _require(await MarketDataApiFacade(session).get_market(market_id), "Market", market_id)
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
    facade = MarketDataApiFacade(session)
    _require(await facade.get_market(market_id), "Market", market_id)
    return _page(await facade.list_market_selections(market_id, pagination), SelectionRead)


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
        await MarketDataApiFacade(session).list_odds_history(filters, pagination), OddsSnapshotRead
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
        await MarketDataApiFacade(session).list_odds_history(filters, pagination), OddsSnapshotRead
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
        await MarketDataApiFacade(session).list_latest_odds(filters, pagination), OddsSnapshotRead
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
        await MarketDataApiFacade(session).list_odds_history(filters, pagination), OddsSnapshotRead
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
        await MarketDataApiFacade(session).list_odds_history(filters, pagination), OddsSnapshotRead
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
    return _page(
        await MarketDataApiFacade(session).list_movements(filters, pagination), OddsMovementRead
    )
