"""Async repository boundary for frozen Feature Store projections and research artifacts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feature_store.models import FeatureDefinition, FeatureSetVersion, FeatureValue
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
from app.modules.research.schemas import DatasetSelection, PaginationParams


class ResearchRepository:
    """All Research persistence and Feature Store read access is isolated in this repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def feature_set_version(self, version_id: UUID) -> FeatureSetVersion | None:
        """Resolve a specific immutable Feature Set version, never a mutable/latest alias."""
        return await self._session.get(FeatureSetVersion, version_id)

    async def feature_values(
        self, *, feature_set_version_id: UUID, selection: DatasetSelection
    ) -> list[tuple[FeatureValue, FeatureDefinition]]:
        """Read canonical Feature Store values once to materialize a frozen dataset projection."""
        statement = (
            select(FeatureValue, FeatureDefinition)
            .join(FeatureDefinition, FeatureDefinition.id == FeatureValue.feature_definition_id)
            .where(FeatureDefinition.feature_set_version_id == feature_set_version_id)
            .where(FeatureDefinition.feature_id.in_(selection.feature_ids))
        )
        if selection.fixture_id:
            statement = statement.where(FeatureValue.fixture_id == selection.fixture_id)
        if selection.team_id:
            statement = statement.where(FeatureValue.team_id == selection.team_id)
        if selection.player_id:
            statement = statement.where(FeatureValue.player_id == selection.player_id)
        if selection.competition_id:
            statement = statement.where(FeatureValue.competition_id == selection.competition_id)
        if selection.season_id:
            statement = statement.where(FeatureValue.season_id == selection.season_id)
        if selection.observed_after:
            statement = statement.where(FeatureValue.observed_at >= selection.observed_after)
        if selection.observed_before:
            statement = statement.where(FeatureValue.observed_at <= selection.observed_before)
        statement = statement.order_by(
            FeatureValue.observed_at,
            FeatureValue.created_at,
            FeatureValue.id,
        )
        return list((await self._session.execute(statement)).all())

    async def existing_dataset(self, idempotency_key: str) -> DatasetSnapshot | None:
        """Return an identical frozen dataset rather than duplicating its immutable rows."""
        return await self._session.scalar(
            select(DatasetSnapshot).where(DatasetSnapshot.idempotency_key == idempotency_key)
        )

    async def dataset_by_code_version(self, code: str, version: str) -> DatasetSnapshot | None:
        """Resolve a named dataset version to detect immutable version conflicts."""
        return await self._session.scalar(
            select(DatasetSnapshot).where(
                DatasetSnapshot.dataset_code == code,
                DatasetSnapshot.version == version,
            )
        )

    async def create_dataset(self, dataset: DatasetSnapshot) -> DatasetSnapshot:
        self._session.add(dataset)
        await self._session.flush()
        return dataset

    async def list_datasets(
        self, pagination: PaginationParams
    ) -> tuple[list[DatasetSnapshot], int]:
        return await self._page(
            select(DatasetSnapshot).order_by(DatasetSnapshot.created_at.desc()), pagination
        )

    async def dataset(self, dataset_id: UUID) -> DatasetSnapshot | None:
        return await self._session.get(DatasetSnapshot, dataset_id)

    async def dataset_rows(
        self, dataset_id: UUID, pagination: PaginationParams
    ) -> tuple[list[DatasetSnapshotRow], int]:
        return await self._page(
            select(DatasetSnapshotRow)
            .where(DatasetSnapshotRow.dataset_snapshot_id == dataset_id)
            .order_by(
                DatasetSnapshotRow.feature_id, DatasetSnapshotRow.observed_at, DatasetSnapshotRow.id
            ),
            pagination,
        )

    async def all_dataset_rows(self, dataset_id: UUID) -> list[DatasetSnapshotRow]:
        """Load a frozen set once for in-process deterministic statistics, never live features."""
        return list(
            (
                await self._session.scalars(
                    select(DatasetSnapshotRow)
                    .where(DatasetSnapshotRow.dataset_snapshot_id == dataset_id)
                    .order_by(DatasetSnapshotRow.feature_id, DatasetSnapshotRow.id)
                )
            ).all()
        )

    async def existing_experiment(self, idempotency_key: str) -> ResearchExperiment | None:
        return await self._session.scalar(
            select(ResearchExperiment).where(ResearchExperiment.idempotency_key == idempotency_key)
        )

    async def experiment_by_code(self, code: str) -> ResearchExperiment | None:
        return await self._session.scalar(
            select(ResearchExperiment).where(ResearchExperiment.experiment_code == code)
        )

    async def create_experiment(self, experiment: ResearchExperiment) -> ResearchExperiment:
        self._session.add(experiment)
        await self._session.flush()
        return experiment

    async def list_experiments(
        self, pagination: PaginationParams
    ) -> tuple[list[ResearchExperiment], int]:
        return await self._page(
            select(ResearchExperiment).order_by(ResearchExperiment.created_at.desc()), pagination
        )

    async def experiment(self, experiment_id: UUID) -> ResearchExperiment | None:
        return await self._session.get(ResearchExperiment, experiment_id)

    async def results(self, experiment_id: UUID) -> list[ExperimentStatisticResult]:
        return list(
            (
                await self._session.scalars(
                    select(ExperimentStatisticResult)
                    .where(ExperimentStatisticResult.experiment_id == experiment_id)
                    .order_by(ExperimentStatisticResult.result_key)
                )
            ).all()
        )

    async def lineage(self, experiment_id: UUID) -> ExperimentLineage | None:
        return await self._session.scalar(
            select(ExperimentLineage).where(ExperimentLineage.experiment_id == experiment_id)
        )

    async def validation(self, experiment_id: UUID) -> list[ExperimentValidationRecord]:
        return list(
            (
                await self._session.scalars(
                    select(ExperimentValidationRecord)
                    .where(ExperimentValidationRecord.experiment_id == experiment_id)
                    .order_by(ExperimentValidationRecord.rule_name)
                )
            ).all()
        )

    async def hypothesis_by_code(self, code: str) -> ResearchHypothesis | None:
        return await self._session.scalar(
            select(ResearchHypothesis).where(ResearchHypothesis.hypothesis_code == code)
        )

    async def hypothesis(self, hypothesis_id: UUID) -> ResearchHypothesis | None:
        return await self._session.get(ResearchHypothesis, hypothesis_id)

    async def statistic_result(self, result_id: UUID) -> ExperimentStatisticResult | None:
        return await self._session.get(ExperimentStatisticResult, result_id)

    async def create_hypothesis(self, hypothesis: ResearchHypothesis) -> ResearchHypothesis:
        self._session.add(hypothesis)
        await self._session.flush()
        return hypothesis

    async def list_hypotheses(
        self, pagination: PaginationParams
    ) -> tuple[list[ResearchHypothesis], int]:
        return await self._page(
            select(ResearchHypothesis).order_by(ResearchHypothesis.created_at.desc()), pagination
        )

    async def create_hypothesis_evaluation(
        self, evaluation: HypothesisEvaluation
    ) -> HypothesisEvaluation:
        self._session.add(evaluation)
        await self._session.flush()
        return evaluation

    async def hypothesis_evaluations(self, hypothesis_id: UUID) -> list[HypothesisEvaluation]:
        return list(
            (
                await self._session.scalars(
                    select(HypothesisEvaluation)
                    .where(HypothesisEvaluation.hypothesis_id == hypothesis_id)
                    .order_by(HypothesisEvaluation.created_at.desc())
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
