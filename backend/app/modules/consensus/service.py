"""Consensus orchestration over compatible immutable Probability outputs only."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.confidence import metrics as confidence_metrics
from app.modules.consensus.disagreement import metrics as disagreement_metrics
from app.modules.consensus.engines import ConsensusEstimate
from app.modules.consensus.enums import ConsensusRunStatus, ConsensusValidationStatus
from app.modules.consensus.exceptions import ConsensusResolutionError, ConsensusVersionConflictError
from app.modules.consensus.lineage import build_lineage, fingerprint
from app.modules.consensus.models import (
    ConsensusOutput,
    ConsensusRun,
    ConsensusRunInput,
    ConsensusValidationRecord,
)
from app.modules.consensus.registry import ConsensusStrategyRegistry
from app.modules.consensus.repositories import ConsensusRepository
from app.modules.consensus.schemas import ConsensusRunCreate
from app.modules.consensus.validation import validate


class ConsensusService:
    def __init__(
        self, session: AsyncSession, registry: ConsensusStrategyRegistry | None = None
    ) -> None:
        self._session = session
        self._repository = ConsensusRepository(session)
        self._registry = registry or ConsensusStrategyRegistry()

    async def create_run(self, request: ConsensusRunCreate) -> ConsensusRun:
        strategy = self._registry.resolve(request.strategy.value)
        inputs = await self._repository.probability_runs(request.probability_run_ids)
        inputs.sort(key=lambda item: str(item.id))
        if not inputs:
            raise ConsensusResolutionError("No requested Probability runs were found.")
        checksum = fingerprint(
            {
                "runs": request.probability_run_ids,
                "strategy": request.strategy,
                "parameters": request.parameters,
                "seed": request.random_seed,
                "input_checksums": [item.input_checksum for item in inputs],
            }
        )
        key = fingerprint({"run_code": request.run_code, "input": checksum})
        existing = await self._repository.existing_run(key)
        if existing is not None:
            return existing
        if await self._repository.run_by_code(request.run_code) is not None:
            raise ConsensusVersionConflictError(
                "Consensus run code is immutable; use a new code for changed inputs."
            )
        try:
            strategy.combine(
                [ConsensusEstimate(item.id, 0.5) for item in inputs], request.parameters
            )
            strategy_valid = True
        except ValueError:
            strategy_valid = False
        findings = validate(
            inputs=inputs,
            expected_count=len(request.probability_run_ids),
            strategy_valid=strategy_valid,
        )
        valid = all(item.status is ConsensusValidationStatus.PASSED for item in findings)
        feature_set_version_id = (
            inputs[0].feature_set_version_id if inputs else request.probability_run_ids[0]
        )
        dataset_snapshot_id = (
            inputs[0].dataset_snapshot_id if inputs else request.probability_run_ids[0]
        )
        run = await self._repository.create_run(
            ConsensusRun(
                run_code=request.run_code,
                feature_set_version_id=feature_set_version_id,
                dataset_snapshot_id=dataset_snapshot_id,
                strategy=request.strategy,
                parameters=request.parameters,
                random_seed=request.random_seed,
                status=ConsensusRunStatus.COMPLETED
                if valid
                else ConsensusRunStatus.VALIDATION_FAILED,
                input_checksum=checksum,
                idempotency_key=key,
            )
        )
        self._session.add_all(
            [
                ConsensusRunInput(
                    consensus_run_id=run.id,
                    probability_run_id=item.id,
                    model_identifier=item.model_identifier,
                    model_version=item.model_version,
                    calibration_version=str(item.calibration_version_id)
                    if item.calibration_version_id
                    else None,
                    research_experiment_id=item.research_experiment_id,
                )
                for item in inputs
            ]
        )
        self._session.add_all(
            [
                ConsensusValidationRecord(
                    consensus_run_id=run.id,
                    rule_name=item.rule_name,
                    status=item.status,
                    message=item.message,
                )
                for item in findings
            ]
        )
        if inputs:
            self._session.add(
                build_lineage(
                    run_id=run.id,
                    feature_set_version_id=run.feature_set_version_id,
                    dataset_snapshot_id=run.dataset_snapshot_id,
                    inputs=inputs,
                    parameters=request.parameters,
                    random_seed=request.random_seed,
                )
            )
        if not valid:
            return run
        outputs = await self._repository.probability_outputs([item.id for item in inputs])
        evaluations = await self._repository.latest_evaluations([item.id for item in inputs])
        quality = _calibration_quality(evaluations, inputs)
        grouped: dict[tuple[object, str, str], list[object]] = {}
        for output in outputs:
            grouped.setdefault((output.fixture_id, output.market_type, output.outcome), []).append(
                output
            )
        self._session.add_all(
            [
                _output(run, key, items, len(inputs), strategy, request.parameters, quality)
                for key, items in grouped.items()
            ]
        )
        return run


def _output(
    run: ConsensusRun,
    key: tuple[object, str, str],
    outputs: list[object],
    expected: int,
    strategy: object,
    parameters: dict[str, object],
    quality: float,
) -> ConsensusOutput:
    estimates = [
        ConsensusEstimate(item.probability_run_id, float(item.estimated_probability))
        for item in outputs
    ]
    probability = strategy.combine(estimates, parameters)
    disagreement = disagreement_metrics([item.probability for item in estimates])
    confidence, confidence_detail, level = confidence_metrics(
        disagreement=disagreement, calibration_quality=quality, completeness=len(outputs) / expected
    )
    return ConsensusOutput(
        consensus_run_id=run.id,
        fixture_id=key[0],
        market_type=key[1],
        outcome=key[2],
        consensus_probability=_decimal(probability),
        confidence_score=_decimal(confidence),
        disagreement_score=_decimal(min(1.0, disagreement["standard_deviation"] / 0.5)),
        agreement_level=level,
        confidence_metrics=confidence_detail,
        disagreement_metrics=disagreement,
        contributor_count=len(outputs),
        expected_count=expected,
    )


def _calibration_quality(evaluations: list[object], inputs: list[object]) -> float:
    latest: dict[object, object] = {}
    for evaluation in evaluations:
        latest.setdefault(evaluation.probability_run_id, evaluation)
    qualities = [
        max(0.0, 1 - float(latest[item.id].metrics.get("brier_score", 0.5)))
        if item.id in latest
        else 0.5
        for item in inputs
    ]
    return sum(qualities) / len(qualities) if qualities else 0.0


def _decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.00000001"))
