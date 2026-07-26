"""Thin API facade preserving Explainability Engine dependencies."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.explainability.registry import ExplainabilityRegistry
from app.modules.explainability.repositories import ExplainabilityRepository
from app.modules.explainability.service import ExplainabilityService


class ExplainabilityApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = (
            ExplainabilityRepository(session),
            ExplainabilityService(session),
        )

    @staticmethod
    def engines():
        return ExplainabilityRegistry().engines()

    async def create_run(self, body: object):
        return await self._service.create_run(body)

    async def explanations(self, id: object):
        return await self._reads.explanations(id)

    async def contributions(self, id: object):
        return await self._reads.contributions(id)

    async def evidence(self, id: object):
        return await self._reads.evidence(id)

    async def reasoning(self, id: object):
        return await self._reads.reasoning(id)

    async def lineage(self, id: object):
        return await self._reads.lineage(id)

    async def validation(self, id: object):
        return await self._reads.validation(id)
