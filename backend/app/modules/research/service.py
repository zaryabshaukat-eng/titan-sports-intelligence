"""Service for immutable dataset snapshots, experiments, and hypothesis evidence."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.research.datasets import build_snapshot_rows
from app.modules.research.enums import ExperimentStatus, ValidationStatus
from app.modules.research.exceptions import (
    DatasetResolutionError,
    DatasetVersionConflictError,
    ExperimentVersionConflictError,
    ResearchValidationError,
)
from app.modules.research.experiments import numeric_analysis_inputs
from app.modules.research.hypotheses import significance_from_p_value, validate_decision
from app.modules.research.lineage import build_experiment_lineage, fingerprint
from app.modules.research.models import (
    DatasetSnapshot,
    ExperimentStatisticResult,
    ExperimentValidationRecord,
    HypothesisEvaluation,
    ResearchExperiment,
    ResearchHypothesis,
)
from app.modules.research.registry import AnalysisRegistry
from app.modules.research.repositories import ResearchRepository
from app.modules.research.schemas import (
    DatasetSnapshotCreate,
    ExperimentCreate,
    HypothesisCreate,
    HypothesisEvaluationCreate,
)
from app.modules.research.validation import validate_experiment


class ResearchService:
    """Coordinates reproducible research without live data or prediction models."""

    def __init__(self, session: AsyncSession, registry: AnalysisRegistry | None = None) -> None:
        self._session = session
        self._repository = ResearchRepository(session)
        self._registry = registry or AnalysisRegistry()

    async def create_dataset(self, request: DatasetSnapshotCreate) -> DatasetSnapshot:
        """Materialize a dataset from one Feature Set version and immutable source rows."""
        feature_set_version = await self._repository.feature_set_version(
            request.feature_set_version_id
        )
        if feature_set_version is None:
            raise DatasetResolutionError("Feature Set version was not found.")
        source_rows = await self._repository.feature_values(
            feature_set_version_id=request.feature_set_version_id,
            selection=request.selection,
        )
        if not source_rows:
            raise ResearchValidationError("Dataset selection produced no Feature Store values.")
        selection = request.selection.model_dump(mode="json")
        source_manifest = [
            {
                "feature_value_id": value.id,
                "feature_definition_id": definition.id,
                "feature_id": definition.feature_id,
                "value": value.value,
                "numeric_value": value.numeric_value,
                "observed_at": value.observed_at,
                "calculated_at": value.calculated_at,
            }
            for value, definition in source_rows
        ]
        checksum = fingerprint(source_manifest)
        generator_versions = {"feature_store": feature_set_version.generator_version}
        idempotency_key = fingerprint(
            {
                "dataset_code": request.dataset_code,
                "version": request.version,
                "feature_set_version": request.feature_set_version_id,
                "selection": selection,
                "checksum": checksum,
            }
        )
        existing = await self._repository.existing_dataset(idempotency_key)
        if existing is not None:
            return existing
        versioned = await self._repository.dataset_by_code_version(
            request.dataset_code, request.version
        )
        if versioned is not None:
            raise DatasetVersionConflictError(
                "Dataset code/version is immutable; use a new version for different source inputs."
            )
        dataset = await self._repository.create_dataset(
            DatasetSnapshot(
                dataset_code=request.dataset_code,
                version=request.version,
                name=request.name,
                description=request.description,
                owner=request.owner,
                feature_set_version_id=request.feature_set_version_id,
                selection=selection,
                generator_versions=generator_versions,
                source_value_count=len(source_rows),
                checksum=checksum,
                idempotency_key=idempotency_key,
            )
        )
        self._session.add_all(
            build_snapshot_rows(dataset_snapshot_id=dataset.id, source_rows=source_rows)
        )
        return dataset

    async def create_experiment(self, request: ExperimentCreate) -> ResearchExperiment:
        """Execute one approved statistical method against an immutable dataset."""
        dataset = await self._repository.dataset(request.dataset_snapshot_id)
        if dataset is None:
            raise DatasetResolutionError("Dataset snapshot was not found.")
        parameters = {
            **request.parameters,
            "analysis": request.analysis.model_dump(mode="json"),
        }
        input_checksum = fingerprint(
            {
                "dataset_checksum": dataset.checksum,
                "feature_set_version": request.feature_set_version_id,
                "generator_versions": dataset.generator_versions,
                "parameters": parameters,
                "random_seed": request.random_seed,
            }
        )
        idempotency_key = fingerprint(
            {"experiment_code": request.experiment_code, "input_checksum": input_checksum}
        )
        existing = await self._repository.existing_experiment(idempotency_key)
        if existing is not None:
            return existing
        code_conflict = await self._repository.experiment_by_code(request.experiment_code)
        if code_conflict is not None:
            raise ExperimentVersionConflictError(
                "Experiment code is immutable; use a new code for different configuration."
            )
        rows = await self._repository.all_dataset_rows(dataset.id)
        values, keyed_values = numeric_analysis_inputs(rows)
        findings = validate_experiment(
            dataset_feature_set_version_id=dataset.feature_set_version_id,
            requested_feature_set_version_id=request.feature_set_version_id,
            analysis=request.analysis,
            selected_feature_ids={row.feature_id for row in rows},
            numeric_feature_counts={key: len(series) for key, series in values.items()},
        )
        valid = all(finding.status is ValidationStatus.PASSED for finding in findings)
        experiment = await self._repository.create_experiment(
            ResearchExperiment(
                experiment_code=request.experiment_code,
                name=request.name,
                description=request.description,
                owner=request.owner,
                feature_set_version_id=request.feature_set_version_id,
                dataset_snapshot_id=dataset.id,
                generator_versions=dataset.generator_versions,
                parameters=parameters,
                random_seed=request.random_seed,
                status=ExperimentStatus.COMPLETED if valid else ExperimentStatus.VALIDATION_FAILED,
                input_checksum=input_checksum,
                idempotency_key=idempotency_key,
            )
        )
        self._session.add_all(
            [
                ExperimentValidationRecord(
                    experiment_id=experiment.id,
                    rule_name=finding.rule_name,
                    status=finding.status,
                    message=finding.message,
                )
                for finding in findings
            ]
        )
        self._session.add(
            build_experiment_lineage(
                experiment_id=experiment.id,
                dataset_snapshot_id=dataset.id,
                feature_set_version_id=request.feature_set_version_id,
                generator_versions=dataset.generator_versions,
                parameters=parameters,
                random_seed=request.random_seed,
            )
        )
        if not valid:
            return experiment
        result = self._registry.execute(
            analysis_type=request.analysis.analysis_type,
            feature_id=request.analysis.feature_id,
            related_feature_id=request.analysis.related_feature_id,
            values=values,
            keyed_values=keyed_values,
            bins=request.analysis.bins,
        )
        self._session.add(
            ExperimentStatisticResult(
                experiment_id=experiment.id,
                result_key=result.result_key,
                analysis_type=request.analysis.analysis_type,
                feature_id=request.analysis.feature_id,
                related_feature_id=request.analysis.related_feature_id,
                method=result.method,
                values=result.values,
                numeric_value=_decimal(result.numeric_value),
                sample_size=result.sample_size,
                confidence_interval_low=_decimal(result.confidence_interval_low),
                confidence_interval_high=_decimal(result.confidence_interval_high),
                p_value=_decimal(result.p_value),
            )
        )
        return experiment

    async def create_hypothesis(self, request: HypothesisCreate) -> ResearchHypothesis:
        """Register a hypothesis without overwriting prior research intent."""
        existing = await self._repository.hypothesis_by_code(request.hypothesis_code)
        if existing is not None:
            if (
                existing.statement == request.statement
                and existing.description == request.description
                and existing.owner == request.owner
            ):
                return existing
            raise ExperimentVersionConflictError(
                "Hypothesis code is immutable; use a new code for a changed statement."
            )
        return await self._repository.create_hypothesis(
            ResearchHypothesis(
                hypothesis_code=request.hypothesis_code,
                statement=request.statement,
                description=request.description,
                owner=request.owner,
            )
        )

    async def evaluate_hypothesis(
        self, request: HypothesisEvaluationCreate
    ) -> HypothesisEvaluation:
        """Attach reviewed results and evidence to immutable research artifacts."""
        if await self._repository.hypothesis(request.hypothesis_id) is None:
            raise DatasetResolutionError("Hypothesis was not found.")
        if await self._repository.experiment(request.experiment_id) is None:
            raise DatasetResolutionError("Experiment was not found.")
        if request.statistic_result_id is not None:
            statistic = await self._repository.statistic_result(request.statistic_result_id)
            if statistic is None or statistic.experiment_id != request.experiment_id:
                raise ResearchValidationError(
                    "Statistic result does not belong to the selected experiment."
                )
        implied_significance = significance_from_p_value(request.p_value)
        significance = request.statistical_significance
        if (
            significance is not None
            and implied_significance is not None
            and significance != implied_significance
        ):
            raise ResearchValidationError(
                "Statistical significance conflicts with the supplied p-value."
            )
        resolved_significance = significance if significance is not None else implied_significance
        if not validate_decision(request.decision, resolved_significance):
            raise ResearchValidationError(
                "The requested hypothesis decision lacks supporting significance."
            )
        return await self._repository.create_hypothesis_evaluation(
            HypothesisEvaluation(
                hypothesis_id=request.hypothesis_id,
                experiment_id=request.experiment_id,
                statistic_result_id=request.statistic_result_id,
                result=request.result,
                evidence=request.evidence,
                statistical_significance=resolved_significance,
                p_value=request.p_value,
                decision=request.decision,
            )
        )


def _decimal(value: float | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None
