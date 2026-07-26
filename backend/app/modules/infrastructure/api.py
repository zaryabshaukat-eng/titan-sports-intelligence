from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.infrastructure.monitoring import metrics

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure"])
R = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
W = Annotated[Principal, Depends(require_permissions(Permission.INFRASTRUCTURE_EXECUTE))]


@router.get("/health")
async def health(request: Request, p: R):
    _ = p
    try:
        redis = await request.app.state.redis.ping()
    except Exception:
        redis = False
    return {
        "redis": "ready" if redis else "not_ready",
        "queue": "local_outbox",
        "worker": "configured",
        "scheduler": "configuration_driven",
    }


@router.get("/readiness")
@router.get("/queue-status")
@router.get("/worker-status")
@router.get("/scheduler-status")
@router.get("/lock-status")
@router.get("/monitoring")
@router.get("/validation")
async def status(p: R):
    _ = p
    return {"status": "ok", "metrics": metrics.snapshot()}
