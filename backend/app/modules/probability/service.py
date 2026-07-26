"""Probability application service for immutable calibration, inference, evaluation, and lineage."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.probability.calibration import calibrate, validate_calibration_parameters
from app.modules.probability.engines import RawProbability
from app.modules.probability.enums import ProbabilityRunStatus, ProbabilityValidationStatus
from app.modules.probability.evaluation import evaluate
from app.modules.probability.exceptions import (
    ProbabilityResolutionError,
    ProbabilityValidationError,
    ProbabilityVersionConflictError,
)
from app.modules.probability.inference import fixture_feature_vectors, infer_fixture_probability
from app.modules.probability.lineage import build_lineage, fingerprint
from app.modules.probability.models import (
    CalibrationVersion,
    ProbabilityEvaluation,
    ProbabilityOutput,
    ProbabilityRun,
    ProbabilityValidationRecord,
)
from app.modules.probability.registry import ProbabilityModelRegistry
from app.modules.probability.repositories import ProbabilityRepository
from app.modules.probability.schemas import (
    CalibrationVersionCreate,
    ProbabilityEvaluationCreate,
    ProbabilityRunCreate,
)
from app.modules.probability.validation import validate_run


class ProbabilityService:
    """Coordinates reproducible estimates with no betting, ranking, or publication policy."""

    def __init__(
        self, session: AsyncSession, registry: ProbabilityModelRegistry | None = None
    ) -> None:
        self._session = session
        self._repository = ProbabilityRepository(session)
        self._registry = registry or ProbabilityModelRegistry()

    async def create_calibration(self, request: CalibrationVersionCreate) -> CalibrationVersion:
        """Persist a validated calibration version or safely reuse an exact retry."""
        validate_calibration_parameters(request.method, request.parameters)
        idempotency_key = fingerprint(request.model_dump(mode="json"))
        existing = await self._repository.existing_calibration(idempotency_key)
        if existing is not None:
            return existing
        versioned = await self._repository.calibration_by_code_version(
            request.calibration_code, request.version
        )
        if versioned is not None:
            raise ProbabilityVersionConflictError(
                "Calibration code/version is immutable; use a new version for changed parameters."
            )
        return await self._repository.create_calibration(
            CalibrationVersion(
                calibration_code=request.calibration_code,
                version=request.version,
                method=request.method,
                parameters=request.parameters,
                compatible_model_identifiers=request.compatible_model_identifiers,
                owner=request.owner,
                idempotency_key=idempotency_key,
            )
        )

    async def create_run(self, request: ProbabilityRunCreate) -> ProbabilityRun:
        """Execute a registered baseline over frozen rows and persist complete evidence."""
        dataset = await self._repository.dataset(request.dataset_snapshot_id)
        if dataset is None:
            raise ProbabilityResolutionError("Research dataset snapshot was not found.")
        experiment = await self._repository.experiment(request.research_experiment_id)
        if experiment is None:
            raise ProbabilityResolutionError("Research experiment was not found.")
        model = self._registry.resolve(request.model_identifier, request.model_version)
        calibration = None
        if request.calibration_version_id is not None:
            calibration = await self._repository.calibration(request.calibration_version_id)
            if calibration is None:
                raise ProbabilityResolutionError("Calibration version was not found.")
        input_checksum = fingerprint(
            {
                "dataset_checksum": dataset.checksum,
                "feature_set_version_id": request.feature_set_version_id,
                "research_experiment_id": request.research_experiment_id,
                "research_input_checksum": experiment.input_checksum,
                "model_identifier": request.model_identifier,
                "model_version": request.model_version,
                "calibration": _calibration_label(calibration),
                "parameters": request.parameters,
                "random_seed": request.random_seed,
                "market_type": request.market_type,
                "outcome": request.outcome,
                "prediction_timestamp": request.prediction_timestamp,
            }
        )
        idempotency_key = fingerprint({"run_code": request.run_code, "input": input_checksum})
        existing = await self._repository.existing_run(idempotency_key)
        if existing is not None:
            return existing
        code_conflict = await self._repository.run_by_code(request.run_code)
        if code_conflict is not None:
            raise ProbabilityVersionConflictError(
                "Probability run code is immutable; use a new code for changed configuration."
            )
        rows = await self._repository.dataset_rows(dataset.id)
        vectors = fixture_feature_vectors(rows)
        findings = validate_run(
            dataset=dataset,
            requested_feature_set_version_id=request.feature_set_version_id,
            experiment=experiment,
            model=model,
            parameters=request.parameters,
            vectors=vectors,
            calibration=calibration,
        )
        valid = all(finding.status is ProbabilityValidationStatus.PASSED for finding in findings)
        run = await self._repository.create_run(
            ProbabilityRun(
                run_code=request.run_code,
                dataset_snapshot_id=request.dataset_snapshot_id,
                feature_set_version_id=request.feature_set_version_id,
                research_experiment_id=request.research_experiment_id,
                model_identifier=request.model_identifier,
                model_version=request.model_version,
                calibration_version_id=request.calibration_version_id,
                market_type=request.market_type,
                outcome=request.outcome,
                parameters=request.parameters,
                random_seed=request.random_seed,
                prediction_timestamp=request.prediction_timestamp,
                status=(
                    ProbabilityRunStatus.COMPLETED
                    if valid
                    else ProbabilityRunStatus.VALIDATION_FAILED
                ),
                input_checksum=input_checksum,
                idempotency_key=idempotency_key,
            )
        )
        self._session.add_all(
            [
                ProbabilityValidationRecord(
                    probability_run_id=run.id,
                    rule_name=finding.rule_name,
                    status=finding.status,
                    message=finding.message,
                )
                for finding in findings
            ]
        )
        self._session.add(
            build_lineage(
                probability_run_id=run.id,
                dataset_snapshot_id=dataset.id,
                feature_set_version_id=request.feature_set_version_id,
                research_experiment_id=request.research_experiment_id,
                model_identifier=request.model_identifier,
                model_version=request.model_version,
                calibration_version=_calibration_label(calibration),
                parameters=request.parameters,
                random_seed=request.random_seed,
            )
        )
        if not valid:
            return run
        self._session.add_all(
            [
                _build_output(
                    run=run,
                    fixture_id=vector.fixture_id,
                    support_count=vector.support_count,
                    raw_probability=infer_fixture_probability(
                        model=model,
                        vector=vector,
                        parameters=request.parameters,
                        random_seed=request.random_seed,
                    ),
                    calibration=calibration,
                )
                for vector in vectors
            ]
        )
        return run

    async def create_evaluation(
        self, run_id: UUID, request: ProbabilityEvaluationCreate
    ) -> ProbabilityEvaluation:
        """Persist repeatable evaluation metrics for explicit output/observed-outcome pairs."""
        run = await self._repository.run(run_id)
        if run is None:
            raise ProbabilityResolutionError("Probability run was not found.")
        requested_ids = [sample.probability_output_id for sample in request.samples]
        outputs = await self._repository.outputs_by_ids(requested_ids)
        output_map = {output.id: output for output in outputs}
        if len(output_map) != len(requested_ids) or any(
            output_map[output_id].probability_run_id != run.id for output_id in requested_ids
        ):
            raise ProbabilityValidationError(
                "Every evaluation sample must reference an output from the selected "
                "probability run."
            )
        evidence = [
            {
                "output_id": sample.probability_output_id,
                "probability": output_map[sample.probability_output_id].estimated_probability,
                "observed_outcome": sample.observed_outcome,
            }
            for sample in request.samples
        ]
        input_checksum = fingerprint(
            {
                "run_input_checksum": run.input_checksum,
                "samples": evidence,
                "reliability_bins": request.reliability_bins,
            }
        )
        idempotency_key = fingerprint(
            {"run_id": run.id, "evaluation_code": request.evaluation_code, "input": input_checksum}
        )
        existing = await self._repository.existing_evaluation(idempotency_key)
        if existing is not None:
            return existing
        code_conflict = await self._repository.evaluation_by_code(run.id, request.evaluation_code)
        if code_conflict is not None:
            raise ProbabilityVersionConflictError(
                "Evaluation code is immutable for a run; use a new code for different observations."
            )
        metrics, reliability = evaluate(
            [
                (
                    float(output_map[sample.probability_output_id].estimated_probability),
                    sample.observed_outcome,
                )
                for sample in request.samples
            ],
            bins=request.reliability_bins,
        )
        return await self._repository.create_evaluation(
            ProbabilityEvaluation(
                probability_run_id=run.id,
                evaluation_code=request.evaluation_code,
                sample_count=len(request.samples),
                metrics=metrics,
                reliability=reliability,
                input_checksum=input_checksum,
                idempotency_key=idempotency_key,
            )
        )


def _build_output(
    *,
    run: ProbabilityRun,
    fixture_id: UUID,
    support_count: int,
    raw_probability: tuple[RawProbability, float, float],
    calibration: CalibrationVersion | None,
) -> ProbabilityOutput:
    """Calibrate a baseline estimate and preserve a matching calibrated confidence interval."""
    raw, raw_low, raw_high = raw_probability
    probability = raw.probability
    low = raw_low
    high = raw_high
    if calibration is not None:
        probability = calibrate(
            probability, method=calibration.method, parameters=calibration.parameters
        )
        low = calibrate(low, method=calibration.method, parameters=calibration.parameters)
        high = calibrate(high, method=calibration.method, parameters=calibration.parameters)
    return ProbabilityOutput(
        probability_run_id=run.id,
        fixture_id=fixture_id,
        market_type=run.market_type,
        outcome=run.outcome,
        estimated_probability=_decimal(probability),
        confidence_interval_low=_decimal(min(low, probability)),
        confidence_interval_high=_decimal(max(high, probability)),
        calibration_version=_calibration_label(calibration),
        prediction_timestamp=run.prediction_timestamp,
        support_count=max(1, support_count),
    )


def _calibration_label(calibration: CalibrationVersion | None) -> str | None:
    return f"{calibration.calibration_code}:{calibration.version}" if calibration else None


def _decimal(value: float) -> Decimal:
    return Decimal(str(value))
