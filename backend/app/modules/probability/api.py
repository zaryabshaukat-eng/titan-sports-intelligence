"""Protected APIs for immutable Probability Engine computation and evidence retrieval."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.probability.exceptions import (
    ProbabilityResolutionError,
    ProbabilityValidationError,
    ProbabilityVersionConflictError,
)
from app.modules.probability.registry import ProbabilityModelRegistry
from app.modules.probability.repositories import ProbabilityRepository
from app.modules.probability.schemas import (
    CalibrationVersionCreate,
    CalibrationVersionRead,
    ModelMetadataRead,
    Page,
    PaginationParams,
    ProbabilityEvaluationCreate,
    ProbabilityEvaluationRead,
    ProbabilityLineageRead,
    ProbabilityOutputRead,
    ProbabilityRunCreate,
    ProbabilityRunRead,
    ProbabilityValidationRead,
)
from app.modules.probability.service import ProbabilityService
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/probability", tags=["Probability"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReadPrincipal = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipal = Annotated[Principal, Depends(require_permissions(Permission.PROBABILITY_EXECUTE))]
PaginationDependency = Annotated[PaginationParams, Depends()]


@router.get(
    "/models",
    response_model=list[ModelMetadataRead],
    summary="List registered probability models",
)
async def list_models(principal: ReadPrincipal) -> list[ModelMetadataRead]:
    """Expose reviewed model metadata without exposing training or provider internals."""
    _ = principal
    return [
        ModelMetadataRead(
            model_identifier=metadata.model_identifier,
            version=metadata.version,
            algorithm=metadata.algorithm,
            description=metadata.description,
            parameter_schema=metadata.parameter_schema,
        )
        for metadata in ProbabilityModelRegistry().metadata()
    ]


@router.post(
    "/calibrations",
    response_model=CalibrationVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register an immutable calibration version",
)
async def create_calibration(
    body: CalibrationVersionCreate,
    session: SessionDependency,
    principal: WritePrincipal,
) -> CalibrationVersionRead:
    """Persist Platt, isotonic, or temperature calibration parameters with their compatibility."""
    _ = principal
    try:
        return CalibrationVersionRead.model_validate(
            await ProbabilityService(session).create_calibration(body)
        )
    except ProbabilityVersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="probability_calibration_version_immutable"
        ) from exc
    except ProbabilityValidationError as exc:
        raise HTTPException(status_code=422, detail="probability_calibration_invalid") from exc


@router.get(
    "/calibrations",
    response_model=Page[CalibrationVersionRead],
    summary="List immutable calibration versions",
)
async def list_calibrations(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[CalibrationVersionRead]:
    _ = principal
    items, total = await ProbabilityRepository(session).list_calibrations(pagination)
    return Page(
        items=[CalibrationVersionRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "/runs",
    response_model=ProbabilityRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an immutable probability run",
)
async def create_run(
    body: ProbabilityRunCreate,
    session: SessionDependency,
    principal: WritePrincipal,
) -> ProbabilityRunRead:
    """Run one selected model only over a frozen Research dataset snapshot."""
    _ = principal
    try:
        return ProbabilityRunRead.model_validate(await ProbabilityService(session).create_run(body))
    except ProbabilityResolutionError as exc:
        raise HTTPException(status_code=404, detail="probability_dependency_not_found") from exc
    except ProbabilityVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="probability_run_immutable") from exc


@router.get(
    "/runs",
    response_model=Page[ProbabilityRunRead],
    summary="List immutable probability runs",
)
async def list_runs(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[ProbabilityRunRead]:
    _ = principal
    items, total = await ProbabilityRepository(session).list_runs(pagination)
    return Page(
        items=[ProbabilityRunRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/runs/{probability_run_id}/outputs",
    response_model=list[ProbabilityOutputRead],
    summary="Retrieve immutable fixture probability estimates",
)
async def list_outputs(
    probability_run_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[ProbabilityOutputRead]:
    _ = principal
    return [
        ProbabilityOutputRead.model_validate(item)
        for item in await ProbabilityRepository(session).outputs(probability_run_id)
    ]


@router.post(
    "/runs/{probability_run_id}/evaluations",
    response_model=ProbabilityEvaluationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Persist immutable probability evaluation metrics",
)
async def create_evaluation(
    probability_run_id: UUID,
    body: ProbabilityEvaluationCreate,
    session: SessionDependency,
    principal: WritePrincipal,
) -> ProbabilityEvaluationRead:
    """Compute scores only from supplied observed outcomes and this run's frozen outputs."""
    _ = principal
    try:
        return ProbabilityEvaluationRead.model_validate(
            await ProbabilityService(session).create_evaluation(probability_run_id, body)
        )
    except ProbabilityResolutionError as exc:
        raise HTTPException(status_code=404, detail="probability_run_not_found") from exc
    except ProbabilityVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="probability_evaluation_immutable") from exc
    except ProbabilityValidationError as exc:
        raise HTTPException(status_code=422, detail="probability_evaluation_invalid") from exc


@router.get(
    "/runs/{probability_run_id}/evaluations",
    response_model=list[ProbabilityEvaluationRead],
    summary="Retrieve immutable evaluation results",
)
async def list_evaluations(
    probability_run_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[ProbabilityEvaluationRead]:
    _ = principal
    return [
        ProbabilityEvaluationRead.model_validate(item)
        for item in await ProbabilityRepository(session).evaluations(probability_run_id)
    ]


@router.get(
    "/runs/{probability_run_id}/lineage",
    response_model=ProbabilityLineageRead | None,
    summary="Retrieve probability run reproducibility lineage",
)
async def get_lineage(
    probability_run_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> ProbabilityLineageRead | None:
    _ = principal
    lineage = await ProbabilityRepository(session).lineage(probability_run_id)
    return ProbabilityLineageRead.model_validate(lineage) if lineage else None


@router.get(
    "/runs/{probability_run_id}/validation",
    response_model=list[ProbabilityValidationRead],
    summary="Retrieve probability compatibility validation evidence",
)
async def list_validation(
    probability_run_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[ProbabilityValidationRead]:
    _ = principal
    return [
        ProbabilityValidationRead.model_validate(item)
        for item in await ProbabilityRepository(session).validation(probability_run_id)
    ]
