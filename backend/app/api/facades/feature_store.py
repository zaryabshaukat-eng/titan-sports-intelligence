"""Thin API facade preserving Feature Store generation and retrieval behavior."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feature_store.repositories import FeatureStoreRepository
from app.modules.feature_store.service import FeatureGenerationService


class FeatureStoreApiFacade:
    """Delegate API calls to the existing immutable Feature Store interfaces."""

    def __init__(self, session: AsyncSession, registry: object | None = None) -> None:
        self._reads = FeatureStoreRepository(session)
        self._service = (
            FeatureGenerationService(session, registry) if registry is not None else None
        )

    async def generate(self, body: object) -> object:
        if self._service is None:
            raise RuntimeError("A feature generator registry is required for generation.")
        return await self._service.generate(body)

    async def feature_sets(self, page: object) -> tuple[list[object], int]:
        return await self._reads.feature_sets(page)

    async def versions(self, code: str) -> list[object]:
        return await self._reads.versions(code)

    async def definitions(self, code: str, version: str) -> list[object]:
        return await self._reads.definitions(code, version)

    async def values(self, filters: object, page: object) -> tuple[list[object], int]:
        return await self._reads.page_values(filters, page)

    async def lineage(self, id: object) -> list[object]:
        return await self._reads.lineage(id)

    async def validation(self, id: object) -> list[object]:
        return await self._reads.validation(id)
