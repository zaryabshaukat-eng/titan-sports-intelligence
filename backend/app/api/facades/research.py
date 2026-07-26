"""Thin API facade preserving immutable Research Engine behavior."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.research.repositories import ResearchRepository
from app.modules.research.service import ResearchService


class ResearchApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = ResearchRepository(session), ResearchService(session)

    async def create_dataset(self, body: object):
        return await self._service.create_dataset(body)

    async def datasets(self, page: object):
        return await self._reads.list_datasets(page)

    async def dataset_rows(self, id: object, page: object):
        return await self._reads.dataset_rows(id, page)

    async def create_experiment(self, body: object):
        return await self._service.create_experiment(body)

    async def experiments(self, page: object):
        return await self._reads.list_experiments(page)

    async def results(self, id: object):
        return await self._reads.results(id)

    async def lineage(self, id: object):
        return await self._reads.lineage(id)

    async def validation(self, id: object):
        return await self._reads.validation(id)

    async def create_hypothesis(self, body: object):
        return await self._service.create_hypothesis(body)

    async def hypotheses(self, page: object):
        return await self._reads.list_hypotheses(page)

    async def evaluate_hypothesis(self, body: object):
        return await self._service.evaluate_hypothesis(body)

    async def hypothesis_evaluations(self, id: object):
        return await self._reads.hypothesis_evaluations(id)
