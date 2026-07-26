from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.improvement import ImprovementApiFacade
from app.core.security import Principal, require_permissions
from app.modules.continuous_improvement.models import (
    CandidateFeature,
    CandidateModel,
    LineageRecord,
    Recommendation,
    RecommendationEvidence,
    ValidationRecord,
)
from app.modules.continuous_improvement.schemas import RunCreate, RunRead
from app.modules.identity.models import Permission
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/continuous-improvement", tags=["Continuous Improvement"])
Session = Annotated[AsyncSession, Depends(get_db_session)]
Reader = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
Writer = Annotated[
    Principal, Depends(require_permissions(Permission.CONTINUOUS_IMPROVEMENT_EXECUTE))
]


@router.post("/run", response_model=RunRead, status_code=status.HTTP_201_CREATED)
async def run(body: RunCreate, session: Session, principal: Writer) -> RunRead:
    _ = principal
    try:
        return RunRead.model_validate(await ImprovementApiFacade(session).run(body))
    except ValueError as exc:
        raise HTTPException(422, "improvement_lineage_invalid") from exc


@router.get("/runs", response_model=list[RunRead])
async def runs(session: Session, principal: Reader) -> list[RunRead]:
    _ = principal
    return [RunRead.model_validate(item) for item in await ImprovementApiFacade(session).runs()]


@router.get("/runs/{run_id}", response_model=RunRead)
async def detail(run_id: UUID, session: Session, principal: Reader) -> RunRead:
    _ = principal
    item = await ImprovementApiFacade(session).get(run_id)
    if item is None:
        raise HTTPException(404, "improvement_run_not_found")
    return RunRead.model_validate(item)


async def _items(model: object, run_id: UUID, session: AsyncSession) -> list[object]:
    return await ImprovementApiFacade(session).items(model, run_id)


@router.get("/recommendations")
async def recommendations(run_id: UUID, session: Session, principal: Reader) -> list[object]:
    _ = principal
    return await _items(Recommendation, run_id, session)


@router.get("/evidence")
async def evidence(run_id: UUID, session: Session, principal: Reader) -> list[object]:
    _ = principal
    return await _items(RecommendationEvidence, run_id, session)


@router.get("/candidates")
async def candidates(run_id: UUID, session: Session, principal: Reader) -> dict[str, list[object]]:
    _ = principal
    return {
        "models": await _items(CandidateModel, run_id, session),
        "features": await _items(CandidateFeature, run_id, session),
    }


@router.get("/validation")
async def validation(run_id: UUID, session: Session, principal: Reader) -> list[object]:
    _ = principal
    return await _items(ValidationRecord, run_id, session)


@router.get("/lineage")
async def lineage(run_id: UUID, session: Session, principal: Reader) -> list[object]:
    _ = principal
    return await _items(LineageRecord, run_id, session)
