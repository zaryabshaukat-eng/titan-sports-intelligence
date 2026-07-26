"""Async repository boundary for immutable Probability Engine data and upstream snapshots."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.probability.models import (
    CalibrationVersion,
    ProbabilityEvaluation,
    ProbabilityLineage,
    ProbabilityOutput,
    ProbabilityRun,
    ProbabilityValidationRecord,
)
from app.modules.probability.schemas import PaginationParams
from app.modules.research.models import DatasetSnapshot, DatasetSnapshotRow, ResearchExperiment


class ProbabilityRepository:
    """Own Probability persistence while reading Research only through immutable artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def dataset(self, dataset_id: UUID) -> DatasetSnapshot | None:
        return await self._session.get(DatasetSnapshot, dataset_id)

    async def experiment(self, experiment_id: UUID) -> ResearchExperiment | None:
        return await self._session.get(ResearchExperiment, experiment_id)

    async def dataset_rows(self, dataset_id: UUID) -> list[DatasetSnapshotRow]:
        return list(
            (
                await self._session.scalars(
                    select(DatasetSnapshotRow)
                    .where(DatasetSnapshotRow.dataset_snapshot_id == dataset_id)
                    .order_by(DatasetSnapshotRow.fixture_id, DatasetSnapshotRow.feature_id)
                )
            ).all()
        )

    async def calibration(self, calibration_id: UUID) -> CalibrationVersion | None:
        return await self._session.get(CalibrationVersion, calibration_id)

    async def existing_calibration(self, idempotency_key: str) -> CalibrationVersion | None:
        return await self._session.scalar(
            select(CalibrationVersion).where(CalibrationVersion.idempotency_key == idempotency_key)
        )

    async def calibration_by_code_version(
        self, calibration_code: str, version: str
    ) -> CalibrationVersion | None:
        return await self._session.scalar(
            select(CalibrationVersion).where(
                CalibrationVersion.calibration_code == calibration_code,
                CalibrationVersion.version == version,
            )
        )

    async def create_calibration(self, calibration: CalibrationVersion) -> CalibrationVersion:
        self._session.add(calibration)
        await self._session.flush()
        return calibration

    async def list_calibrations(
        self, pagination: PaginationParams
    ) -> tuple[list[CalibrationVersion], int]:
        return await self._page(
            select(CalibrationVersion).order_by(CalibrationVersion.created_at.desc()), pagination
        )

    async def existing_run(self, idempotency_key: str) -> ProbabilityRun | None:
        return await self._session.scalar(
            select(ProbabilityRun).where(ProbabilityRun.idempotency_key == idempotency_key)
        )

    async def run_by_code(self, run_code: str) -> ProbabilityRun | None:
        return await self._session.scalar(
            select(ProbabilityRun).where(ProbabilityRun.run_code == run_code)
        )

    async def create_run(self, run: ProbabilityRun) -> ProbabilityRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def list_runs(self, pagination: PaginationParams) -> tuple[list[ProbabilityRun], int]:
        return await self._page(
            select(ProbabilityRun).order_by(ProbabilityRun.created_at.desc()), pagination
        )

    async def run(self, run_id: UUID) -> ProbabilityRun | None:
        return await self._session.get(ProbabilityRun, run_id)

    async def outputs(self, run_id: UUID) -> list[ProbabilityOutput]:
        return list(
            (
                await self._session.scalars(
                    select(ProbabilityOutput)
                    .where(ProbabilityOutput.probability_run_id == run_id)
                    .order_by(ProbabilityOutput.fixture_id, ProbabilityOutput.market_type)
                )
            ).all()
        )

    async def outputs_by_ids(self, output_ids: Sequence[UUID]) -> list[ProbabilityOutput]:
        if not output_ids:
            return []
        return list(
            (
                await self._session.scalars(
                    select(ProbabilityOutput).where(ProbabilityOutput.id.in_(output_ids))
                )
            ).all()
        )

    async def lineage(self, run_id: UUID) -> ProbabilityLineage | None:
        return await self._session.scalar(
            select(ProbabilityLineage).where(ProbabilityLineage.probability_run_id == run_id)
        )

    async def validation(self, run_id: UUID) -> list[ProbabilityValidationRecord]:
        return list(
            (
                await self._session.scalars(
                    select(ProbabilityValidationRecord)
                    .where(ProbabilityValidationRecord.probability_run_id == run_id)
                    .order_by(ProbabilityValidationRecord.rule_name)
                )
            ).all()
        )

    async def existing_evaluation(self, idempotency_key: str) -> ProbabilityEvaluation | None:
        return await self._session.scalar(
            select(ProbabilityEvaluation).where(
                ProbabilityEvaluation.idempotency_key == idempotency_key
            )
        )

    async def evaluation_by_code(
        self, run_id: UUID, evaluation_code: str
    ) -> ProbabilityEvaluation | None:
        return await self._session.scalar(
            select(ProbabilityEvaluation).where(
                ProbabilityEvaluation.probability_run_id == run_id,
                ProbabilityEvaluation.evaluation_code == evaluation_code,
            )
        )

    async def create_evaluation(self, evaluation: ProbabilityEvaluation) -> ProbabilityEvaluation:
        self._session.add(evaluation)
        await self._session.flush()
        return evaluation

    async def evaluations(self, run_id: UUID) -> list[ProbabilityEvaluation]:
        return list(
            (
                await self._session.scalars(
                    select(ProbabilityEvaluation)
                    .where(ProbabilityEvaluation.probability_run_id == run_id)
                    .order_by(ProbabilityEvaluation.created_at)
                )
            ).all()
        )

    async def _page[EntityT](
        self, statement: Select[tuple[EntityT]], pagination: PaginationParams
    ) -> tuple[list[EntityT], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        rows = list(
            (
                await self._session.scalars(
                    statement.offset(pagination.offset).limit(pagination.limit)
                )
            ).all()
        )
        return rows, total or 0
