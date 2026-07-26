"""Protected internal ingestion and read-only Statistics API."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.statistics import StatisticsApiFacade
from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.statistics.schemas import (
    CategoryRead,
    Page,
    Pagination,
    SnapshotRead,
    StatisticsIngestionRequest,
    StatisticsIngestionResult,
)
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/statistics", tags=["Statistics"])
Session = Annotated[AsyncSession, Depends(get_db_session)]
PrincipalDep = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipalDep = Annotated[Principal, Depends(require_permissions(Permission.STATISTICS_INGEST))]
PageDep = Annotated[Pagination, Depends()]

# Retain the legacy direct-call defaults while declaring injected values precisely.
_DEFAULT_PAGINATION: Pagination = cast(Pagination, None)
_DEFAULT_SESSION: AsyncSession = cast(AsyncSession, None)
_DEFAULT_PRINCIPAL: Principal = cast(Principal, None)


def get_statistics_ingestion_facade(request: Request, session: Session) -> StatisticsApiFacade:
    """Compose the write facade without leaking the provider registry to the route handler."""
    return StatisticsApiFacade(session, request.app.state.statistics_provider_registry)


IngestionFacade = Annotated[StatisticsApiFacade, Depends(get_statistics_ingestion_facade)]


def page(
    items: list[object], total: int, p: Pagination, schema: type[CategoryRead] | type[SnapshotRead]
) -> Page[object]:
    return Page(
        items=[schema.model_validate(x) for x in items], total=total, limit=p.limit, offset=p.offset
    )


@router.post(
    "/ingestion/{provider_name}",
    response_model=StatisticsIngestionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest(
    provider_name: str,
    body: StatisticsIngestionRequest,
    request: Request,
    facade: IngestionFacade,
    principal: WritePrincipalDep,
) -> StatisticsIngestionResult:
    _ = principal
    try:
        result = await facade.ingest(provider_name, body.payloads)
    except KeyError as exc:
        raise HTTPException(404, detail="statistics_provider_not_found") from exc
    metrics = request.app.state.metrics
    if metrics is not None:
        failures = sum(item.outcome == "validation_failed" for item in result.items)
        metrics.observe_ingestion("statistics", provider_name, len(result.items), failures)
    return result


@router.get("/categories", response_model=Page[CategoryRead])
async def categories(p: PageDep, session: Session, principal: PrincipalDep) -> Page[object]:
    _ = principal
    rows, total = await StatisticsApiFacade(session).categories(p)
    return page(rows, total, p, CategoryRead)


async def snapshots(
    fixture_id: UUID | None,
    scope: str | None,
    p: Pagination,
    session: AsyncSession,
    *,
    latest_only: bool = False,
) -> Page[object]:
    rows, total = await StatisticsApiFacade(session).snapshots(
        fixture_id, scope, p, latest_only=latest_only
    )
    return page(rows, total, p, SnapshotRead)


@router.get("/fixture-statistics", response_model=Page[SnapshotRead])
async def fixture_statistics(
    fixture_id: UUID | None = None,
    p: PageDep = _DEFAULT_PAGINATION,
    session: Session = _DEFAULT_SESSION,
    principal: PrincipalDep = _DEFAULT_PRINCIPAL,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, "fixture", p, session)


@router.get("/team-statistics", response_model=Page[SnapshotRead])
async def team_statistics(
    fixture_id: UUID | None = None,
    p: PageDep = _DEFAULT_PAGINATION,
    session: Session = _DEFAULT_SESSION,
    principal: PrincipalDep = _DEFAULT_PRINCIPAL,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, "team", p, session)


@router.get("/player-statistics", response_model=Page[SnapshotRead])
async def player_statistics(
    fixture_id: UUID | None = None,
    p: PageDep = _DEFAULT_PAGINATION,
    session: Session = _DEFAULT_SESSION,
    principal: PrincipalDep = _DEFAULT_PRINCIPAL,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, "player", p, session)


@router.get("/latest", response_model=Page[SnapshotRead])
async def latest(
    fixture_id: UUID | None = None,
    p: PageDep = _DEFAULT_PAGINATION,
    session: Session = _DEFAULT_SESSION,
    principal: PrincipalDep = _DEFAULT_PRINCIPAL,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, None, p, session, latest_only=True)


@router.get("/history", response_model=Page[SnapshotRead])
async def history(
    fixture_id: UUID | None = None,
    p: PageDep = _DEFAULT_PAGINATION,
    session: Session = _DEFAULT_SESSION,
    principal: PrincipalDep = _DEFAULT_PRINCIPAL,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, None, p, session)
