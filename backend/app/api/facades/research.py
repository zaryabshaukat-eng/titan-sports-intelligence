"""Thin API facade preserving immutable Research Engine behavior."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.research.models import (
    DatasetSnapshot,
    DatasetSnapshotRow,
    ExperimentLineage,
    ExperimentStatisticResult,
    ExperimentValidationRecord,
    HypothesisEvaluation,
    ResearchExperiment,
    ResearchHypothesis,
)
from app.modules.research.repositories import ResearchRepository
from app.modules.research.schemas import (
    DatasetSnapshotCreate,
    ExperimentCreate,
    HypothesisCreate,
    HypothesisEvaluationCreate,
    PaginationParams,
)
from app.modules.research.service import ResearchService


class ResearchApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = ResearchRepository(session), ResearchService(session)

    async def create_dataset(self, body: DatasetSnapshotCreate) -> DatasetSnapshot:
        return await self._service.create_dataset(body)

    async def datasets(self, page: PaginationParams) -> tuple[list[DatasetSnapshot], int]:
        return await self._reads.list_datasets(page)

    async def dataset_rows(
        self, id: UUID, page: PaginationParams
    ) -> tuple[list[DatasetSnapshotRow], int]:
        return await self._reads.dataset_rows(id, page)

    async def create_experiment(self, body: ExperimentCreate) -> ResearchExperiment:
        return await self._service.create_experiment(body)

    async def experiments(self, page: PaginationParams) -> tuple[list[ResearchExperiment], int]:
        return await self._reads.list_experiments(page)

    async def results(self, id: UUID) -> list[ExperimentStatisticResult]:
        return await self._reads.results(id)

    async def lineage(self, id: UUID) -> ExperimentLineage | None:
        return await self._reads.lineage(id)

    async def validation(self, id: UUID) -> list[ExperimentValidationRecord]:
        return await self._reads.validation(id)

    async def create_hypothesis(self, body: HypothesisCreate) -> ResearchHypothesis:
        return await self._service.create_hypothesis(body)

    async def hypotheses(self, page: PaginationParams) -> tuple[list[ResearchHypothesis], int]:
        return await self._reads.list_hypotheses(page)

    async def evaluate_hypothesis(self, body: HypothesisEvaluationCreate) -> HypothesisEvaluation:
        return await self._service.evaluate_hypothesis(body)

    async def hypothesis_evaluations(self, id: UUID) -> list[HypothesisEvaluation]:
        return await self._reads.hypothesis_evaluations(id)
