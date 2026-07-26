from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require_permissions
from app.modules.explainability.exceptions import (
    ExplainabilityResolutionError,
    ExplainabilityVersionConflictError,
)
from app.modules.explainability.registry import ExplainabilityRegistry
from app.modules.explainability.repositories import ExplainabilityRepository
from app.modules.explainability.schemas import (
    EvidenceReferenceRead,
    ExplainabilityLineageRead,
    ExplainabilityRunCreate,
    ExplainabilityRunRead,
    ExplainabilityValidationRead,
    ExplainerMetadataRead,
    ExplanationRead,
    FeatureContributionRead,
    ReasoningStepRead,
)
from app.modules.explainability.service import ExplainabilityService
from app.modules.identity.models import Permission
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/explainability", tags=["Explainability"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReadPrincipal = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipal = Annotated[
    Principal, Depends(require_permissions(Permission.EXPLAINABILITY_EXECUTE))
]


@router.get("/engines", response_model=list[ExplainerMetadataRead])
async def engines(principal: ReadPrincipal) -> list[ExplainerMetadataRead]:
    _ = principal
    return [
        ExplainerMetadataRead(
            identifier=item.metadata.identifier, description=item.metadata.description
        )
        for item in ExplainabilityRegistry().engines()
    ]


@router.post("/runs", response_model=ExplainabilityRunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    body: ExplainabilityRunCreate, session: SessionDependency, principal: WritePrincipal
) -> ExplainabilityRunRead:
    _ = principal
    try:
        return ExplainabilityRunRead.model_validate(
            await ExplainabilityService(session).create_run(body)
        )
    except ExplainabilityResolutionError as exc:
        raise HTTPException(status_code=404, detail="explainability_dependency_not_found") from exc
    except ExplainabilityVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="explainability_run_immutable") from exc


@router.get("/runs/{run_id}/explanations", response_model=list[ExplanationRead])
async def explanations(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[ExplanationRead]:
    _ = principal
    return [
        ExplanationRead.model_validate(item)
        for item in await ExplainabilityRepository(session).explanations(run_id)
    ]


@router.get("/explanations/{id}/contributions", response_model=list[FeatureContributionRead])
async def contributions(
    id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[FeatureContributionRead]:
    _ = principal
    return [
        FeatureContributionRead.model_validate(item)
        for item in await ExplainabilityRepository(session).contributions(id)
    ]


@router.get("/explanations/{id}/evidence", response_model=list[EvidenceReferenceRead])
async def evidence(
    id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[EvidenceReferenceRead]:
    _ = principal
    return [
        EvidenceReferenceRead.model_validate(item)
        for item in await ExplainabilityRepository(session).evidence(id)
    ]


@router.get("/explanations/{id}/reasoning", response_model=list[ReasoningStepRead])
async def reasoning(
    id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[ReasoningStepRead]:
    _ = principal
    return [
        ReasoningStepRead.model_validate(item)
        for item in await ExplainabilityRepository(session).reasoning(id)
    ]


@router.get("/runs/{id}/lineage", response_model=ExplainabilityLineageRead | None)
async def lineage(
    id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> ExplainabilityLineageRead | None:
    _ = principal
    item = await ExplainabilityRepository(session).lineage(id)
    return ExplainabilityLineageRead.model_validate(item) if item else None


@router.get("/runs/{id}/validation", response_model=list[ExplainabilityValidationRead])
async def validation(
    id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[ExplainabilityValidationRead]:
    _ = principal
    return [
        ExplainabilityValidationRead.model_validate(item)
        for item in await ExplainabilityRepository(session).validation(id)
    ]
