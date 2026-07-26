"""Thin API facade preserving Probability Engine service, registry, and read behavior."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.probability.registry import ProbabilityModelRegistry
from app.modules.probability.repositories import ProbabilityRepository
from app.modules.probability.service import ProbabilityService


class ProbabilityApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = ProbabilityRepository(session), ProbabilityService(session)

    @staticmethod
    def models():
        return ProbabilityModelRegistry().metadata()

    async def create_calibration(self, body: object):
        return await self._service.create_calibration(body)

    async def calibrations(self, page: object):
        return await self._reads.list_calibrations(page)

    async def create_run(self, body: object):
        return await self._service.create_run(body)

    async def runs(self, page: object):
        return await self._reads.list_runs(page)

    async def outputs(self, id: object):
        return await self._reads.outputs(id)

    async def create_evaluation(self, id: object, body: object):
        return await self._service.create_evaluation(id, body)

    async def evaluations(self, id: object):
        return await self._reads.evaluations(id)

    async def lineage(self, id: object):
        return await self._reads.lineage(id)

    async def validation(self, id: object):
        return await self._reads.validation(id)
