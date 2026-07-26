"""Thin API facade preserving Risk Engine dependencies."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.risk.registry import RiskAnalyzerRegistry
from app.modules.risk.repositories import RiskRepository
from app.modules.risk.service import RiskService


class RiskApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = RiskRepository(session), RiskService(session)

    @staticmethod
    def analyzers():
        return RiskAnalyzerRegistry().analyzers()

    async def create_run(self, body: object):
        return await self._service.create_run(body)

    async def outputs(self, id: object):
        return await self._reads.outputs(id)

    async def lineage(self, id: object):
        return await self._reads.lineage(id)

    async def validation(self, id: object):
        return await self._reads.validation(id)
