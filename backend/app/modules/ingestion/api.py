"""Protected internal REST adapter for fixture-ingestion requests."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require_authenticated_principal
from app.modules.ingestion.exceptions import UnknownProviderError
from app.modules.ingestion.providers.registry import FixtureProviderRegistry
from app.modules.ingestion.schemas import FixtureIngestionBatchResult, FixtureIngestionRequest
from app.modules.ingestion.service import FixtureIngestionService
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/ingestion", tags=["Fixture Ingestion"])

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
PrincipalDependency = Annotated[Principal, Depends(require_authenticated_principal)]


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
    session: SessionDependency,
    principal: PrincipalDependency,
) -> FixtureIngestionBatchResult:
    """Run one registered provider adapter inside the request-scoped database transaction."""
    _ = principal  # Authorization policy will be added to this protected boundary later.
    registry: FixtureProviderRegistry = request.app.state.fixture_provider_registry
    try:
        adapter = registry.get(provider_name)
    except UnknownProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ingestion_provider_not_found",
                "message": f"Fixture provider '{provider_name}' is not registered.",
            },
        ) from exc

    return await FixtureIngestionService(session=session, provider_adapter=adapter).ingest(
        request_body.payloads
    )
