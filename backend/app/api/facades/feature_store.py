"""Thin API facade preserving Feature Store generation and retrieval behavior."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feature_store.models import (
    FeatureDefinition,
    FeatureLineage,
    FeatureSet,
    FeatureSetVersion,
    FeatureValidationRecord,
    FeatureValue,
)
from app.modules.feature_store.registry import FeatureGeneratorRegistry
from app.modules.feature_store.repositories import FeatureStoreRepository
from app.modules.feature_store.schemas import (
    FeatureGenerationRequest,
    FeatureGenerationResult,
    FeatureValueFilters,
    PaginationParams,
)
from app.modules.feature_store.service import FeatureGenerationService


class FeatureStoreApiFacade:
    """Delegate API calls to the existing immutable Feature Store interfaces."""

    def __init__(
        self, session: AsyncSession, registry: FeatureGeneratorRegistry | None = None
    ) -> None:
        self._reads = FeatureStoreRepository(session)
        self._service = (
            FeatureGenerationService(session, registry) if registry is not None else None
        )

    async def generate(self, body: FeatureGenerationRequest) -> FeatureGenerationResult:
        if self._service is None:
            raise RuntimeError("A feature generator registry is required for generation.")
        return await self._service.generate(body)

    async def feature_sets(self, page: PaginationParams) -> tuple[list[FeatureSet], int]:
        return await self._reads.feature_sets(page)

    async def versions(self, code: str) -> list[FeatureSetVersion]:
        return await self._reads.versions(code)

    async def definitions(self, code: str, version: str) -> list[FeatureDefinition]:
        return await self._reads.definitions(code, version)

    async def values(
        self, filters: FeatureValueFilters, page: PaginationParams
    ) -> tuple[list[FeatureValue], int]:
        return await self._reads.page_values(filters, page)

    async def lineage(self, id: UUID) -> list[FeatureLineage]:
        return await self._reads.lineage(id)

    async def validation(self, id: UUID) -> list[FeatureValidationRecord]:
        return await self._reads.validation(id)
