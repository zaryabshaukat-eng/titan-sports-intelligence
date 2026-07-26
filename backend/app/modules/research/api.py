"""Protected internal Research Engine APIs for immutable datasets, experiments, and hypotheses."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.research import ResearchApiFacade
from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.research.exceptions import (
    DatasetResolutionError,
    DatasetVersionConflictError,
    ExperimentVersionConflictError,
    ResearchValidationError,
)
from app.modules.research.schemas import (
    DatasetSnapshotCreate,
    DatasetSnapshotRead,
    DatasetSnapshotRowRead,
    ExperimentCreate,
    ExperimentLineageRead,
    ExperimentRead,
    ExperimentValidationRead,
    HypothesisCreate,
    HypothesisEvaluationCreate,
    HypothesisEvaluationRead,
    HypothesisRead,
    Page,
    PaginationParams,
    StatisticResultRead,
)
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/research", tags=["Research"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReadPrincipal = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipal = Annotated[Principal, Depends(require_permissions(Permission.RESEARCH_EXECUTE))]
PaginationDependency = Annotated[PaginationParams, Depends()]


@router.post(
    "/datasets",
    response_model=DatasetSnapshotRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an immutable Feature Store dataset snapshot",
)
async def create_dataset(
    body: DatasetSnapshotCreate,
    session: SessionDependency,
    principal: WritePrincipal,
) -> DatasetSnapshotRead:
    """Copy explicitly versioned Feature Store observations into a frozen research dataset."""
    _ = principal
    try:
        return DatasetSnapshotRead.model_validate(
            await ResearchApiFacade(session).create_dataset(body)
        )
    except DatasetResolutionError as exc:
        raise HTTPException(
            status_code=404, detail="research_feature_set_version_not_found"
        ) from exc
    except DatasetVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="research_dataset_version_immutable") from exc
    except ResearchValidationError as exc:
        raise HTTPException(status_code=422, detail="research_dataset_selection_invalid") from exc


@router.get("/datasets", response_model=Page[DatasetSnapshotRead], summary="List research datasets")
async def list_datasets(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[DatasetSnapshotRead]:
    _ = principal
    items, total = await ResearchApiFacade(session).datasets(pagination)
    return Page(
        items=[DatasetSnapshotRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/datasets/{dataset_snapshot_id}/rows",
    response_model=Page[DatasetSnapshotRowRead],
    summary="Retrieve materialized dataset rows",
)
async def list_dataset_rows(
    dataset_snapshot_id: UUID,
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[DatasetSnapshotRowRead]:
    _ = principal
    items, total = await ResearchApiFacade(session).dataset_rows(dataset_snapshot_id, pagination)
    return Page(
        items=[DatasetSnapshotRowRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "/experiments",
    response_model=ExperimentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute an immutable statistical experiment",
)
async def create_experiment(
    body: ExperimentCreate,
    session: SessionDependency,
    principal: WritePrincipal,
) -> ExperimentRead:
    """Run a reviewed statistical method only against a frozen dataset snapshot."""
    _ = principal
    try:
        return ExperimentRead.model_validate(
            await ResearchApiFacade(session).create_experiment(body)
        )
    except DatasetResolutionError as exc:
        raise HTTPException(status_code=404, detail="research_dataset_not_found") from exc
    except ExperimentVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="research_experiment_immutable") from exc


@router.get(
    "/experiments", response_model=Page[ExperimentRead], summary="List immutable experiments"
)
async def list_experiments(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[ExperimentRead]:
    _ = principal
    items, total = await ResearchApiFacade(session).experiments(pagination)
    return Page(
        items=[ExperimentRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/experiments/{experiment_id}/statistics",
    response_model=list[StatisticResultRead],
    summary="Retrieve immutable experiment statistics",
)
async def experiment_statistics(
    experiment_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[StatisticResultRead]:
    _ = principal
    return [
        StatisticResultRead.model_validate(item)
        for item in await ResearchApiFacade(session).results(experiment_id)
    ]


@router.get(
    "/experiments/{experiment_id}/lineage",
    response_model=ExperimentLineageRead | None,
    summary="Retrieve experiment reproducibility lineage",
)
async def experiment_lineage(
    experiment_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> ExperimentLineageRead | None:
    _ = principal
    lineage = await ResearchApiFacade(session).lineage(experiment_id)
    return ExperimentLineageRead.model_validate(lineage) if lineage else None


@router.get(
    "/experiments/{experiment_id}/validation",
    response_model=list[ExperimentValidationRead],
    summary="Retrieve experiment validation evidence",
)
async def experiment_validation(
    experiment_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[ExperimentValidationRead]:
    _ = principal
    return [
        ExperimentValidationRead.model_validate(item)
        for item in await ResearchApiFacade(session).validation(experiment_id)
    ]


@router.post(
    "/hypotheses",
    response_model=HypothesisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register an immutable research hypothesis",
)
async def create_hypothesis(
    body: HypothesisCreate,
    session: SessionDependency,
    principal: WritePrincipal,
) -> HypothesisRead:
    _ = principal
    try:
        return HypothesisRead.model_validate(
            await ResearchApiFacade(session).create_hypothesis(body)
        )
    except ExperimentVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="research_hypothesis_immutable") from exc


@router.get("/hypotheses", response_model=Page[HypothesisRead], summary="List research hypotheses")
async def list_hypotheses(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[HypothesisRead]:
    _ = principal
    items, total = await ResearchApiFacade(session).hypotheses(pagination)
    return Page(
        items=[HypothesisRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "/hypotheses/evaluations",
    response_model=HypothesisEvaluationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Attach immutable evidence to a hypothesis",
)
async def evaluate_hypothesis(
    body: HypothesisEvaluationCreate,
    session: SessionDependency,
    principal: WritePrincipal,
) -> HypothesisEvaluationRead:
    _ = principal
    try:
        return HypothesisEvaluationRead.model_validate(
            await ResearchApiFacade(session).evaluate_hypothesis(body)
        )
    except DatasetResolutionError as exc:
        raise HTTPException(status_code=404, detail="research_artifact_not_found") from exc
    except ResearchValidationError as exc:
        raise HTTPException(status_code=422, detail="research_hypothesis_evidence_invalid") from exc


@router.get(
    "/hypotheses/{hypothesis_id}/evaluations",
    response_model=list[HypothesisEvaluationRead],
    summary="Retrieve hypothesis evaluation history",
)
async def hypothesis_evaluations(
    hypothesis_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[HypothesisEvaluationRead]:
    _ = principal
    return [
        HypothesisEvaluationRead.model_validate(item)
        for item in await ResearchApiFacade(session).hypothesis_evaluations(hypothesis_id)
    ]
