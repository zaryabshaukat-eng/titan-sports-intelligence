from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.monitoring import MonitoringApiFacade
from app.core.security import Principal, require_permissions
from app.modules.evaluation_monitoring.models import (
    Alert,
    CalibrationHealth,
    DriftMeasurement,
    FeatureHealth,
    LineageRecord,
    ModelHealth,
    ProviderHealth,
    RunArtifact,
    ValidationRecord,
)
from app.modules.evaluation_monitoring.schemas import (
    AlertRead,
    LineageRead,
    MonitoringRunCreate,
    RunRead,
    ValidationRead,
)
from app.modules.identity.models import Permission
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/evaluation-monitoring", tags=["Continuous Evaluation"])
S = Annotated[AsyncSession, Depends(get_db_session)]
R = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
W = Annotated[Principal, Depends(require_permissions(Permission.EVALUATION_MONITORING_EXECUTE))]


@router.post("/run", response_model=RunRead, status_code=status.HTTP_201_CREATED)
async def run(body: MonitoringRunCreate, s: S, p: W) -> RunRead:
    _ = p
    try:
        return RunRead.model_validate(await MonitoringApiFacade(s).run(body))
    except ValueError as e:
        raise HTTPException(422, "monitoring_lineage_invalid") from e


@router.get("/runs", response_model=list[RunRead])
async def runs(s: S, p: R) -> list[RunRead]:
    _ = p
    return [RunRead.model_validate(x) for x in await MonitoringApiFacade(s).runs()]


@router.get("/runs/{id}", response_model=RunRead)
async def detail(id: UUID, s: S, p: R) -> RunRead:
    _ = p
    value = await MonitoringApiFacade(s).get(id)
    if value is None:
        raise HTTPException(404, "evaluation_run_not_found")
    return RunRead.model_validate(value)


async def _items(model: type[RunArtifact], id: UUID, s: AsyncSession) -> list[RunArtifact]:
    return await MonitoringApiFacade(s).items(model, id)


@router.get("/drift")
async def drift(run_id: UUID, s: S, p: R):
    _ = p
    return await _items(DriftMeasurement, run_id, s)


@router.get("/provider-health")
async def provider_health(run_id: UUID, s: S, p: R):
    _ = p
    return await _items(ProviderHealth, run_id, s)


@router.get("/model-health")
async def model_health(run_id: UUID, s: S, p: R):
    _ = p
    return await _items(ModelHealth, run_id, s)


@router.get("/feature-health")
async def feature_health(run_id: UUID, s: S, p: R):
    _ = p
    return await _items(FeatureHealth, run_id, s)


@router.get("/calibration-health")
async def calibration_health(run_id: UUID, s: S, p: R):
    _ = p
    return await _items(CalibrationHealth, run_id, s)


@router.get("/history", response_model=list[RunRead])
async def history(s: S, p: R) -> list[RunRead]:
    _ = p
    return [RunRead.model_validate(x) for x in await MonitoringApiFacade(s).runs()]


@router.get("/alerts", response_model=list[AlertRead])
async def alerts(run_id: UUID, s: S, p: R) -> list[AlertRead]:
    _ = p
    return [AlertRead.model_validate(x) for x in await _items(Alert, run_id, s)]


@router.get("/validation", response_model=list[ValidationRead])
async def validation(run_id: UUID, s: S, p: R) -> list[ValidationRead]:
    _ = p
    return [ValidationRead.model_validate(x) for x in await _items(ValidationRecord, run_id, s)]


@router.get("/lineage", response_model=list[LineageRead])
async def lineage(run_id: UUID, s: S, p: R) -> list[LineageRead]:
    _ = p
    return [LineageRead.model_validate(x) for x in await _items(LineageRecord, run_id, s)]
