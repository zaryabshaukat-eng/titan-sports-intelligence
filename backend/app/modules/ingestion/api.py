"""Protected internal REST adapter for fixture-ingestion requests."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.ingestion import IngestionApiFacade
from app.core.security import Principal, require_permissions
from app.modules.identity.models import Permission
from app.modules.ingestion.exceptions import UnknownProviderError
from app.modules.ingestion.schemas import FixtureIngestionBatchResult, FixtureIngestionRequest
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/ingestion", tags=["Fixture Ingestion"])

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
PrincipalDependency = Annotated[Principal, Depends(require_permissions(Permission.FIXTURE_INGEST))]


def get_ingestion_facade(request: Request, session: SessionDependency) -> IngestionApiFacade:
    """Compose the API facade at the transport boundary without exposing a registry to routes."""
    return IngestionApiFacade(session, request.app.state.fixture_provider_registry)


FacadeDependency = Annotated[IngestionApiFacade, Depends(get_ingestion_facade)]


@router.post(
    "/fixtures/{provider_name}",
    response_model=FixtureIngestionBatchResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a provider fixture batch",
    description=(
        "Protected internal endpoint. It stores immutable raw JSON, validates and normalizes it, "
        "upserts the canonical Sports Domain, and writes audit and transactional-outbox records."
    ),
)
async def ingest_fixture_batch(
    provider_name: str,
    request_body: FixtureIngestionRequest,
    request: Request,
    facade: FacadeDependency,
    principal: PrincipalDependency,
) -> FixtureIngestionBatchResult:
    """Run one registered provider adapter inside the request-scoped database transaction."""
    _ = principal  # Authorization policy will be added to this protected boundary later.
    try:
        result = await facade.ingest(provider_name, request_body.payloads)
    except UnknownProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ingestion_provider_not_found",
                "message": f"Fixture provider '{provider_name}' is not registered.",
            },
        ) from exc

    metrics = request.app.state.metrics
    if metrics is not None:
        metrics.observe_ingestion(
            "fixture_ingestion",
            provider_name,
            result.received_count,
            result.failed_count,
        )
    return result
