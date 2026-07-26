"""Protected internal Feature Store generation and read-only retrieval endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.facades.feature_store import FeatureStoreApiFacade
from app.core.security import Principal, require_permissions
from app.modules.feature_store.exceptions import (
    FeatureGenerationResolutionError,
    FeatureSetVersionConflictError,
)
from app.modules.feature_store.schemas import (
    FeatureDefinitionRead,
    FeatureGenerationRequest,
    FeatureGenerationResult,
    FeatureLineageRead,
    FeatureSetRead,
    FeatureSetVersionRead,
    FeatureValidationRead,
    FeatureValueFilters,
    FeatureValueRead,
    Page,
    PaginationParams,
)
from app.modules.identity.models import Permission
from app.shared.persistence.database import get_db_session

router = APIRouter(prefix="/feature-store", tags=["Feature Store"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
ReadPrincipal = Annotated[Principal, Depends(require_permissions(Permission.DATA_READ))]
GeneratePrincipal = Annotated[Principal, Depends(require_permissions(Permission.RESEARCH_EXECUTE))]
PaginationDependency = Annotated[PaginationParams, Depends()]


def get_feature_generation_facade(
    request: Request, session: SessionDependency
) -> FeatureStoreApiFacade:
    """Compose the write facade without exposing a generator registry to routes."""
    return FeatureStoreApiFacade(session, request.app.state.feature_generator_registry)


GenerationFacade = Annotated[FeatureStoreApiFacade, Depends(get_feature_generation_facade)]


@router.post(
    "/generations",
    response_model=FeatureGenerationResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate an immutable Feature Store snapshot",
    description=(
        "Protected offline generation from canonical Sports, Statistics, and Market Data only. "
        "The same inputs and immutable source records safely reuse the existing generation run."
    ),
)
async def generate_features(
    body: FeatureGenerationRequest,
    facade: GenerationFacade,
    principal: GeneratePrincipal,
) -> FeatureGenerationResult:
    """Execute deterministic generation without exposing provider payloads or training a model."""
    _ = principal
    try:
        return await facade.generate(body)
    except FeatureGenerationResolutionError as exc:
        raise HTTPException(status_code=404, detail="feature_store_fixture_not_found") from exc
    except FeatureSetVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="feature_store_version_immutable") from exc


@router.get("/feature-sets", response_model=Page[FeatureSetRead], summary="List Feature Sets")
async def list_feature_sets(
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[FeatureSetRead]:
    """List stable Feature Set identities available for feature lookup or historical rebuilds."""
    _ = principal
    items, total = await FeatureStoreApiFacade(session).feature_sets(pagination)
    return Page(
        items=[FeatureSetRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/feature-sets/{feature_set_code}/versions",
    response_model=list[FeatureSetVersionRead],
    summary="List immutable Feature Set versions",
)
async def list_feature_set_versions(
    feature_set_code: str,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[FeatureSetVersionRead]:
    """Return version and generator metadata required for reproducible downstream consumers."""
    _ = principal
    return [
        FeatureSetVersionRead.model_validate(item)
        for item in await FeatureStoreApiFacade(session).versions(feature_set_code)
    ]


@router.get(
    "/feature-sets/{feature_set_code}/versions/{feature_set_version}/definitions",
    response_model=list[FeatureDefinitionRead],
    summary="List immutable Feature Set definitions",
)
async def list_feature_definitions(
    feature_set_code: str,
    feature_set_version: str,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[FeatureDefinitionRead]:
    """Expose complete versioned metadata required to interpret feature values exactly."""
    _ = principal
    return [
        FeatureDefinitionRead.model_validate(item)
        for item in await FeatureStoreApiFacade(session).definitions(
            feature_set_code, feature_set_version
        )
    ]


@router.get(
    "/features", response_model=Page[FeatureValueRead], summary="Retrieve immutable features"
)
async def list_features(
    filters: Annotated[FeatureValueFilters, Depends()],
    pagination: PaginationDependency,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> Page[FeatureValueRead]:
    """Query immutable values by any canonical subject, timestamp window, and feature version."""
    _ = principal
    items, total = await FeatureStoreApiFacade(session).values(filters, pagination)
    return Page(
        items=[FeatureValueRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/features/{feature_value_id}/lineage",
    response_model=list[FeatureLineageRead],
    summary="Retrieve feature lineage",
)
async def feature_lineage(
    feature_value_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[FeatureLineageRead]:
    """Expose canonical source records and calculation logic for one immutable feature value."""
    _ = principal
    return [
        FeatureLineageRead.model_validate(item)
        for item in await FeatureStoreApiFacade(session).lineage(feature_value_id)
    ]


@router.get(
    "/features/{feature_value_id}/validation",
    response_model=list[FeatureValidationRead],
    summary="Retrieve feature validation evidence",
)
async def feature_validation(
    feature_value_id: UUID,
    session: SessionDependency,
    principal: ReadPrincipal,
) -> list[FeatureValidationRead]:
    """Expose null, type, dependency, temporal, and version validation outcomes."""
    _ = principal
    return [
        FeatureValidationRead.model_validate(item)
        for item in await FeatureStoreApiFacade(session).validation(feature_value_id)
    ]
