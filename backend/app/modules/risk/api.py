from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.risk.exceptions import RiskResolutionError, RiskVersionConflictError
from app.modules.risk.registry import RiskAnalyzerRegistry
from app.modules.risk.repositories import RiskRepository
from app.modules.risk.schemas import (
    AnalyzerMetadataRead,
    RiskLineageRead,
    RiskOutputRead,
    RiskRunCreate,
    RiskRunRead,
    RiskValidationRead,
)
from app.modules.risk.service import RiskService
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/risk", tags=["Risk"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReadPrincipal = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
WritePrincipal = Annotated[Principal, Depends(require_permissions(Permission.RISK_EXECUTE))]


@router.get("/analyzers", response_model=list[AnalyzerMetadataRead])
async def analyzers(principal: ReadPrincipal) -> list[AnalyzerMetadataRead]:
    _ = principal
    return [
        AnalyzerMetadataRead(
            identifier=item.metadata.identifier, description=item.metadata.description
        )
        for item in RiskAnalyzerRegistry().analyzers()
    ]


@router.post("/runs", response_model=RiskRunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    body: RiskRunCreate, session: SessionDependency, principal: WritePrincipal
) -> RiskRunRead:
    _ = principal
    try:
        return RiskRunRead.model_validate(await RiskService(session).create_run(body))
    except RiskResolutionError as exc:
        raise HTTPException(status_code=404, detail="risk_consensus_not_found") from exc
    except RiskVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="risk_run_immutable") from exc


@router.get("/runs/{run_id}/outputs", response_model=list[RiskOutputRead])
async def outputs(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[RiskOutputRead]:
    _ = principal
    return [
        RiskOutputRead.model_validate(item)
        for item in await RiskRepository(session).outputs(run_id)
    ]


@router.get("/runs/{run_id}/lineage", response_model=RiskLineageRead | None)
async def lineage(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> RiskLineageRead | None:
    _ = principal
    value = await RiskRepository(session).lineage(run_id)
    return RiskLineageRead.model_validate(value) if value else None


@router.get("/runs/{run_id}/validation", response_model=list[RiskValidationRead])
async def validation(
    run_id: UUID, session: SessionDependency, principal: ReadPrincipal
) -> list[RiskValidationRead]:
    _ = principal
    return [
        RiskValidationRead.model_validate(item)
        for item in await RiskRepository(session).validation(run_id)
    ]
