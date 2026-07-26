"""Thin API facade preserving Consensus Engine dependency boundaries."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.registry import ConsensusStrategyRegistry
from app.modules.consensus.repositories import ConsensusRepository
from app.modules.consensus.service import ConsensusService


class ConsensusApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = ConsensusRepository(session), ConsensusService(session)

    @staticmethod
    def strategies():
        return ConsensusStrategyRegistry().metadata()

    async def create_run(self, body: object):
        return await self._service.create_run(body)

    async def runs(self, page: object):
        return await self._reads.list_runs(page)

    async def outputs(self, id: object):
        return await self._reads.outputs(id)

    async def lineage(self, id: object):
        return await self._reads.lineage(id)

    async def validation(self, id: object):
        return await self._reads.validation(id)
