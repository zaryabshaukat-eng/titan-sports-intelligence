"""Thin API facade preserving deterministic Backtesting dependencies."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.comparisons import compare
from app.modules.evaluation.registry import ScenarioRegistry
from app.modules.evaluation.repositories import EvaluationRepository
from app.modules.evaluation.service import BacktestService


class EvaluationApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = EvaluationRepository(session), BacktestService(session)

    @staticmethod
    def scenarios():
        return ScenarioRegistry().metadata()

    @staticmethod
    def compare(baseline_id: object, candidate_id: object, baseline: object, candidate: object):
        return compare(baseline_id, candidate_id, baseline, candidate)

    async def create(self, body: object):
        return await self._service.create(body)

    async def runs(self, page: object):
        return await self._reads.list_runs(page)

    async def run(self, id: object):
        return await self._reads.run(id)

    async def results(self, id: object):
        return await self._reads.results(id)

    async def metric(self, id: object):
        return await self._reads.metric(id)

    async def comparison_metrics(self, ids: object):
        return await self._reads.comparison_metrics(ids)

    async def lineage(self, id: object):
        return await self._reads.lineage(id)

    async def validation(self, id: object):
        return await self._reads.validation(id)
