from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation_monitoring.repositories import MonitoringRepository
from app.modules.evaluation_monitoring.services import MonitoringService


class MonitoringApiFacade:
    def __init__(self, s: AsyncSession):
        self._reads, self._service = MonitoringRepository(s), MonitoringService(s)

    async def run(self, b: object):
        return await self._service.run(b)

    async def runs(self):
        return await self._reads.runs()

    async def get(self, id: object):
        return await self._reads.run(id)

    async def items(self, m: object, id: object):
        return await self._reads.list_for(m, id)
