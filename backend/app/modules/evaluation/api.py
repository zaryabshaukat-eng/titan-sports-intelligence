from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.evaluation import EvaluationApiFacade
from app.core.security import Principal, require_permissions
from app.modules.evaluation.schemas import (
    BacktestComparisonRead,
    BacktestLineageRead,
    BacktestMetricRead,
    BacktestResultRead,
    BacktestRunCreate,
    BacktestRunRead,
    BacktestValidationRead,
    Page,
    PaginationParams,
    ScenarioMetadataRead,
)
from app.modules.identity.models import Permission
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])
S = Annotated[AsyncSession, Depends(get_db_session)]
R = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
W = Annotated[Principal, Depends(require_permissions(Permission.EVALUATION_EXECUTE))]
P = Annotated[PaginationParams, Depends()]


@router.get("/scenarios", response_model=list[ScenarioMetadataRead])
async def scenarios(p: R) -> list[ScenarioMetadataRead]:
    _ = p
    return [
        ScenarioMetadataRead(identifier=x.identifier, description=x.description)
        for x in EvaluationApiFacade.scenarios()
    ]


@router.post("/backtests", response_model=BacktestRunRead, status_code=status.HTTP_201_CREATED)
async def create(body: BacktestRunCreate, s: S, p: W) -> BacktestRunRead:
    _ = p
    try:
        return BacktestRunRead.model_validate(await EvaluationApiFacade(s).create(body))
    except ValueError as e:
        raise HTTPException(status_code=422, detail="backtest_artifact_or_lineage_invalid") from e


@router.get("/backtests", response_model=Page[BacktestRunRead])
async def list_backtests(pagination: P, s: S, p: R) -> Page[BacktestRunRead]:
    _ = p
    items, total = await EvaluationApiFacade(s).runs(pagination)
    return Page(
        items=[BacktestRunRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/backtests/{id}", response_model=BacktestRunRead)
async def backtest(id: UUID, s: S, p: R) -> BacktestRunRead:
    _ = p
    item = await EvaluationApiFacade(s).run(id)
    if item is None:
        raise HTTPException(status_code=404, detail="backtest_not_found")
    return BacktestRunRead.model_validate(item)


@router.get("/backtests/{id}/results", response_model=list[BacktestResultRead])
async def results(id: UUID, s: S, p: R) -> list[BacktestResultRead]:
    _ = p
    return [BacktestResultRead.model_validate(x) for x in await EvaluationApiFacade(s).results(id)]


@router.get("/backtests/{id}/metrics", response_model=BacktestMetricRead | None)
async def metrics(id: UUID, s: S, p: R) -> BacktestMetricRead | None:
    _ = p
    x = await EvaluationApiFacade(s).metric(id)
    return BacktestMetricRead.model_validate(x) if x else None


@router.get("/comparisons", response_model=BacktestComparisonRead)
async def comparisons(
    baseline_run_id: UUID, candidate_run_id: UUID, s: S, p: R
) -> BacktestComparisonRead:
    _ = p
    values = await EvaluationApiFacade(s).comparison_metrics([baseline_run_id, candidate_run_id])
    if baseline_run_id not in values or candidate_run_id not in values:
        raise HTTPException(status_code=404, detail="backtest_metrics_not_found")
    return BacktestComparisonRead.model_validate(
        EvaluationApiFacade.compare(
            baseline_run_id,
            candidate_run_id,
            values[baseline_run_id].metrics,
            values[candidate_run_id].metrics,
        )
    )


@router.get("/backtests/{id}/lineage", response_model=BacktestLineageRead | None)
async def lineage(id: UUID, s: S, p: R) -> BacktestLineageRead | None:
    _ = p
    x = await EvaluationApiFacade(s).lineage(id)
    return BacktestLineageRead.model_validate(x) if x else None


@router.get("/backtests/{id}/validation", response_model=list[BacktestValidationRead])
async def validation(id: UUID, s: S, p: R) -> list[BacktestValidationRead]:
    _ = p
    return [
        BacktestValidationRead.model_validate(x)
        for x in await EvaluationApiFacade(s).validation(id)
    ]
