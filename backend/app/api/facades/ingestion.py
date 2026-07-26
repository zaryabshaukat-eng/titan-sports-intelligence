from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.providers.registry import FixtureProviderRegistry
from app.modules.ingestion.schemas import FixtureIngestionBatchResult
from app.modules.ingestion.service import FixtureIngestionService


class IngestionApiFacade:
    """Resolve a registered provider and delegate to the frozen ingestion service."""

    def __init__(self, session: AsyncSession, registry: FixtureProviderRegistry) -> None:
        self._session = session
        self._registry = registry

    async def ingest(
        self, provider_name: str, payloads: list[dict[str, Any]]
    ) -> FixtureIngestionBatchResult:
        adapter = self._registry.get(provider_name)
        return await FixtureIngestionService(
            session=self._session, provider_adapter=adapter
        ).ingest(payloads)
