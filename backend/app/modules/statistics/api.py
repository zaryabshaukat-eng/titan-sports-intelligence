"""Protected internal ingestion and read-only Statistics API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.statistics.models import StatisticCategory, StatisticSnapshot
from app.modules.statistics.schemas import (
    CategoryRead,
    Page,
    Pagination,
    SnapshotRead,
    StatisticsIngestionRequest,
    StatisticsIngestionResult,
)
from app.modules.statistics.service import StatisticsIngestionService
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/statistics", tags=["Statistics"])
Session = Annotated[AsyncSession, Depends(get_db_session)]
PrincipalDep = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipalDep = Annotated[Principal, Depends(require_permissions(Permission.STATISTICS_INGEST))]
PageDep = Annotated[Pagination, Depends()]


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
    session: Session,
    principal: WritePrincipalDep,
) -> StatisticsIngestionResult:
    _ = principal
    try:
        adapter = (request.app.state.statistics_provider_registry).get(provider_name)
    except KeyError as exc:
        raise HTTPException(404, detail="statistics_provider_not_found") from exc
    result = await StatisticsIngestionService(session, adapter).ingest(body.payloads)
    metrics = request.app.state.metrics
    if metrics is not None:
        failures = sum(item.outcome == "validation_failed" for item in result.items)
        metrics.observe_ingestion("statistics", provider_name, len(result.items), failures)
    return result


@router.get("/categories", response_model=Page[CategoryRead])
async def categories(p: PageDep, session: Session, principal: PrincipalDep) -> Page[object]:
    _ = principal
    total = await session.scalar(select(func.count()).select_from(StatisticCategory)) or 0
    rows = list(
        (
            await session.scalars(
                select(StatisticCategory)
                .order_by(StatisticCategory.code)
                .offset(p.offset)
                .limit(p.limit)
            )
        ).all()
    )
    return page(rows, total, p, CategoryRead)


async def snapshots(
    fixture_id: UUID | None,
    scope: str | None,
    p: Pagination,
    session: AsyncSession,
    *,
    latest_only: bool = False,
) -> Page[object]:
    q = select(StatisticSnapshot)
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
        q = q.join(ranked, ranked.c.snapshot_id == StatisticSnapshot.id).where(ranked.c.rank == 1)
    if fixture_id:
        q = q.where(StatisticSnapshot.fixture_id == fixture_id)
    if scope:
        q = q.where(StatisticSnapshot.scope == scope)
    count = select(func.count()).select_from(q.order_by(None).subquery())
    total = await session.scalar(count) or 0
    rows = list(
        (
            await session.scalars(
                q.order_by(StatisticSnapshot.observed_at.desc()).offset(p.offset).limit(p.limit)
            )
        ).all()
    )
    return page(rows, total, p, SnapshotRead)


@router.get("/fixture-statistics", response_model=Page[SnapshotRead])
async def fixture_statistics(
    fixture_id: UUID | None = None,
    p: PageDep = None,
    session: Session = None,
    principal: PrincipalDep = None,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, "fixture", p, session)


@router.get("/team-statistics", response_model=Page[SnapshotRead])
async def team_statistics(
    fixture_id: UUID | None = None,
    p: PageDep = None,
    session: Session = None,
    principal: PrincipalDep = None,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, "team", p, session)


@router.get("/player-statistics", response_model=Page[SnapshotRead])
async def player_statistics(
    fixture_id: UUID | None = None,
    p: PageDep = None,
    session: Session = None,
    principal: PrincipalDep = None,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, "player", p, session)


@router.get("/latest", response_model=Page[SnapshotRead])
async def latest(
    fixture_id: UUID | None = None,
    p: PageDep = None,
    session: Session = None,
    principal: PrincipalDep = None,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, None, p, session, latest_only=True)


@router.get("/history", response_model=Page[SnapshotRead])
async def history(
    fixture_id: UUID | None = None,
    p: PageDep = None,
    session: Session = None,
    principal: PrincipalDep = None,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, None, p, session)
