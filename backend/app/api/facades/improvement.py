from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.continuous_improvement.repositories import ImprovementRepository
from app.modules.continuous_improvement.services import ImprovementService


class ImprovementApiFacade:
    def __init__(self, s: AsyncSession):
        self._reads, self._service = ImprovementRepository(s), ImprovementService(s)

    async def run(self, b: object):
        return await self._service.run(b)

    async def runs(self):
        return await self._reads.runs()

    async def get(self, id: object):
        return await self._reads.run(id)

    async def items(self, m: object, id: object):
        return await self._reads.for_run(m, id)
