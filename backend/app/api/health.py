"""Unauthenticated liveness endpoint required by deployment platforms."""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    """Stable liveness response contract."""

    status: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Confirm that the API process is able to receive requests.

    This is deliberately a liveness endpoint. Dependency readiness is monitored
    separately so an infrastructure outage does not prevent diagnostics.
    """
    return HealthResponse(status="ok")
