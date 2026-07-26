"""Thin API facade preserving Probability Engine service, registry, and read behavior."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.probability.engines import ModelMetadata
from app.modules.probability.models import (
    CalibrationVersion,
    ProbabilityEvaluation,
    ProbabilityLineage,
    ProbabilityOutput,
    ProbabilityRun,
    ProbabilityValidationRecord,
)
from app.modules.probability.registry import ProbabilityModelRegistry
from app.modules.probability.repositories import ProbabilityRepository
from app.modules.probability.schemas import (
    CalibrationVersionCreate,
    PaginationParams,
    ProbabilityEvaluationCreate,
    ProbabilityRunCreate,
)
from app.modules.probability.service import ProbabilityService


class ProbabilityApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = ProbabilityRepository(session), ProbabilityService(session)

    @staticmethod
    def models() -> list[ModelMetadata]:
        return ProbabilityModelRegistry().metadata()

    async def create_calibration(self, body: CalibrationVersionCreate) -> CalibrationVersion:
        return await self._service.create_calibration(body)

    async def calibrations(self, page: PaginationParams) -> tuple[list[CalibrationVersion], int]:
        return await self._reads.list_calibrations(page)

    async def create_run(self, body: ProbabilityRunCreate) -> ProbabilityRun:
        return await self._service.create_run(body)

    async def runs(self, page: PaginationParams) -> tuple[list[ProbabilityRun], int]:
        return await self._reads.list_runs(page)

    async def outputs(self, id: UUID) -> list[ProbabilityOutput]:
        return await self._reads.outputs(id)

    async def create_evaluation(
        self, id: UUID, body: ProbabilityEvaluationCreate
    ) -> ProbabilityEvaluation:
        return await self._service.create_evaluation(id, body)

    async def evaluations(self, id: UUID) -> list[ProbabilityEvaluation]:
        return await self._reads.evaluations(id)

    async def lineage(self, id: UUID) -> ProbabilityLineage | None:
        return await self._reads.lineage(id)

    async def validation(self, id: UUID) -> list[ProbabilityValidationRecord]:
        return await self._reads.validation(id)
