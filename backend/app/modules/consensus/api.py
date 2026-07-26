"""Protected Consensus Engine APIs for evidence-only combined probabilities."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.consensus import ConsensusApiFacade
from app.core.security import Principal, require_permissions
from app.modules.consensus.exceptions import ConsensusResolutionError, ConsensusVersionConflictError
from app.modules.consensus.schemas import (
    ConsensusLineageRead,
    ConsensusMetricRead,
    ConsensusOutputRead,
    ConsensusRunCreate,
    ConsensusRunRead,
    ConsensusValidationRead,
    Page,
    PaginationParams,
    StrategyMetadataRead,
)
from app.modules.identity.models import Permission
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/consensus", tags=["Consensus"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReadPrincipal = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipal = Annotated[Principal, Depends(require_permissions(Permission.CONSENSUS_EXECUTE))]
PaginationDependency = Annotated[PaginationParams, Depends()]


@router.get("/strategies", response_model=list[StrategyMetadataRead])
async def strategies(principal: ReadPrincipal) -> list[StrategyMetadataRead]:
    _ = principal
    return [
        StrategyMetadataRead(
            identifier=item.identifier,
            description=item.description,
            parameter_schema=item.parameter_schema,
        )
        for item in ConsensusApiFacade.strategies()
    ]


@router.post("/runs", response_model=ConsensusRunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    body: ConsensusRunCreate, session: SessionDependency, principal: WritePrincipal
) -> ConsensusRunRead:
    _ = principal
    try:
        return ConsensusRunRead.model_validate(await ConsensusApiFacade(session).create_run(body))
    except ConsensusResolutionError as exc:
        raise HTTPException(status_code=404, detail="consensus_probability_runs_not_found") from exc
    except ConsensusVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="consensus_run_immutable") from exc


@router.get("/runs", response_model=Page[ConsensusRunRead])
async def list_runs(
    pagination: PaginationDependency, session: SessionDependency, principal: ReadPrincipal
) -> Page[ConsensusRunRead]:
    _ = principal
    items, total = await ConsensusApiFacade(session).runs(pagination)
    return Page(
        items=[ConsensusRunRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/runs/{run_id}/outputs", response_model=list[ConsensusOutputRead])
async def outputs(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[ConsensusOutputRead]:
    _ = principal
    return [
        ConsensusOutputRead.model_validate(item)
        for item in await ConsensusApiFacade(session).outputs(run_id)
    ]


@router.get("/runs/{run_id}/confidence-metrics", response_model=list[ConsensusMetricRead])
async def confidence(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[ConsensusMetricRead]:
    _ = principal
    return [
        ConsensusMetricRead(
            fixture_id=item.fixture_id,
            market_type=item.market_type,
            outcome=item.outcome,
            metrics=item.confidence_metrics,
        )
        for item in await ConsensusApiFacade(session).outputs(run_id)
    ]


@router.get("/runs/{run_id}/disagreement-metrics", response_model=list[ConsensusMetricRead])
async def disagreement(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[ConsensusMetricRead]:
    _ = principal
    return [
        ConsensusMetricRead(
            fixture_id=item.fixture_id,
            market_type=item.market_type,
            outcome=item.outcome,
            metrics=item.disagreement_metrics,
        )
        for item in await ConsensusApiFacade(session).outputs(run_id)
    ]


@router.get("/runs/{run_id}/lineage", response_model=ConsensusLineageRead | None)
async def lineage(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> ConsensusLineageRead | None:
    _ = principal
    value = await ConsensusApiFacade(session).lineage(run_id)
    return ConsensusLineageRead.model_validate(value) if value else None


@router.get("/runs/{run_id}/validation", response_model=list[ConsensusValidationRead])
async def validation(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[ConsensusValidationRead]:
    _ = principal
    return [
        ConsensusValidationRead.model_validate(item)
        for item in await ConsensusApiFacade(session).validation(run_id)
    ]
