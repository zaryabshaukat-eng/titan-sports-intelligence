"""Protected internal ingestion and read-only Statistics API."""

# ruff: noqa: E501, E701, E702
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require_authenticated_principal
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
PrincipalDep = Annotated[Principal, Depends(require_authenticated_principal)]
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
    principal: PrincipalDep,
) -> StatisticsIngestionResult:
    _ = principal
    try:
        adapter = (request.app.state.statistics_provider_registry).get(provider_name)
    except KeyError as exc:
        raise HTTPException(404, detail="statistics_provider_not_found") from exc
    return await StatisticsIngestionService(session, adapter).ingest(body.payloads)


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
    fixture_id: UUID | None, scope: str | None, p: Pagination, session: AsyncSession
) -> Page[object]:
    q = select(StatisticSnapshot)
    count = select(func.count()).select_from(StatisticSnapshot)
    if fixture_id:
        q, count = (
            q.where(StatisticSnapshot.fixture_id == fixture_id),
            count.where(StatisticSnapshot.fixture_id == fixture_id),
        )
    if scope:
        q, count = (
            q.where(StatisticSnapshot.scope == scope),
            count.where(StatisticSnapshot.scope == scope),
        )
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
    return await snapshots(fixture_id, None, p, session)


@router.get("/history", response_model=Page[SnapshotRead])
async def history(
    fixture_id: UUID | None = None,
    p: PageDep = None,
    session: Session = None,
    principal: PrincipalDep = None,
) -> Page[object]:
    _ = principal
    return await snapshots(fixture_id, None, p, session)
