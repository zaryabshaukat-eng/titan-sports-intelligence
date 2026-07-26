"""Thin API facade preserving deterministic Backtesting dependencies."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.comparisons import compare
from app.modules.evaluation.models import (
    BacktestLineage,
    BacktestMetric,
    BacktestResult,
    BacktestRun,
    BacktestValidationRecord,
)
from app.modules.evaluation.registry import ScenarioRegistry
from app.modules.evaluation.repositories import EvaluationRepository
from app.modules.evaluation.scenarios import ScenarioMetadata
from app.modules.evaluation.schemas import BacktestRunCreate, PaginationParams
from app.modules.evaluation.service import BacktestService


class EvaluationApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = EvaluationRepository(session), BacktestService(session)

    @staticmethod
    def scenarios() -> list[ScenarioMetadata]:
        return ScenarioRegistry().metadata()

    @staticmethod
    def compare(
        baseline_id: UUID,
        candidate_id: UUID,
        baseline: dict[str, object],
        candidate: dict[str, object],
    ) -> dict[str, object]:
        return compare(baseline_id, candidate_id, baseline, candidate)

    async def create(self, body: BacktestRunCreate) -> BacktestRun:
        return await self._service.create(body)

    async def runs(self, page: PaginationParams) -> tuple[list[BacktestRun], int]:
        return await self._reads.list_runs(page)

    async def run(self, id: UUID) -> BacktestRun | None:
        return await self._reads.run(id)

    async def results(self, id: UUID) -> list[BacktestResult]:
        return await self._reads.results(id)

    async def metric(self, id: UUID) -> BacktestMetric | None:
        return await self._reads.metric(id)

    async def comparison_metrics(self, ids: list[UUID]) -> dict[UUID, BacktestMetric]:
        return await self._reads.comparison_metrics(ids)

    async def lineage(self, id: UUID) -> BacktestLineage | None:
        return await self._reads.lineage(id)

    async def validation(self, id: UUID) -> list[BacktestValidationRecord]:
        return await self._reads.validation(id)
