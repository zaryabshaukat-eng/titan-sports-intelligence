"""Unit coverage for deterministic Probability Engine inference and immutable evidence."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.modules.probability.calibration import calibrate, validate_calibration_parameters
from app.modules.probability.ensemble import EnsembleMember, weighted_probability
from app.modules.probability.enums import CalibrationMethod, ProbabilityRunStatus
from app.modules.probability.evaluation import evaluate
from app.modules.probability.exceptions import (
    ProbabilityValidationError,
    ProbabilityVersionConflictError,
)
from app.modules.probability.registry import ProbabilityModelRegistry
from app.modules.probability.schemas import (
    CalibrationVersionCreate,
    EvaluationSample,
    ProbabilityEvaluationCreate,
    ProbabilityRunCreate,
)
from app.modules.probability.service import ProbabilityService


def test_baseline_inference_calibration_ensemble_and_evaluation_are_deterministic() -> None:
    """All initial computation is pure, reproducible, and independent from provider payloads."""
    model = ProbabilityModelRegistry().resolve("logistic_baseline", "1.0.0")
    raw = model.infer(
        features={"home_form": 2.0},
        parameters={"weights": {"home_form": 0.5}, "intercept": 0},
        random_seed=42,
    )
    calibrated = calibrate(
        raw.probability,
        method=CalibrationMethod.PLATT,
        parameters={"a": 1.0, "b": 0.0},
    )
    isotonic = calibrate(
        0.25,
        method=CalibrationMethod.ISOTONIC,
        parameters={
            "points": [
                {"prediction": 0.0, "calibrated": 0.1},
                {"prediction": 0.5, "calibrated": 0.5},
                {"prediction": 1.0, "calibrated": 0.9},
            ]
        },
    )
    metrics, reliability = evaluate([(0.8, True), (0.2, False), (0.6, True)], bins=2)

    assert raw.probability == calibrated
    assert isotonic == pytest.approx(0.3)
    assert (
        weighted_probability(
            [
                EnsembleMember("model_a", 0.25, 1),
                EnsembleMember("model_b", 0.75, 3),
            ]
        )
        == 0.625
    )
    assert 0 <= float(metrics["brier_score"]) <= 1
    assert metrics["roc_auc"] == 1.0
    assert sum(item["count"] for item in reliability) == 3


def test_calibration_validation_rejects_non_monotonic_or_non_positive_parameters() -> None:
    """Calibration versions cannot persist parameters that would break reproducible semantics."""
    with pytest.raises(ProbabilityValidationError):
        validate_calibration_parameters(CalibrationMethod.PLATT, {"a": 0, "b": 0})
    with pytest.raises(ProbabilityValidationError):
        validate_calibration_parameters(
            CalibrationMethod.ISOTONIC,
            {
                "points": [
                    {"prediction": 0.0, "calibrated": 0.6},
                    {"prediction": 0.5, "calibrated": 0.4},
                ]
            },
        )
    with pytest.raises(ProbabilityValidationError):
        weighted_probability([EnsembleMember("model_a", 0.4, 0)])


def test_probability_service_persists_reproducible_runs_outputs_lineage_and_evaluation() -> None:
    """Exact retries reuse artifacts; incompatible models become evidence-bearing failed runs."""
    now = datetime(2026, 8, 1, tzinfo=UTC)
    feature_set_version_id = uuid4()
    dataset_id = uuid4()
    experiment_id = uuid4()
    fixture_ids = (uuid4(), uuid4())

    class _Session:
        def __init__(self) -> None:
            self.added: list[object] = []

        def add(self, item: object) -> None:
            if getattr(item, "id", None) is None:
                item.id = uuid4()
            self.added.append(item)

        def add_all(self, items: list[object]) -> None:
            for item in items:
                self.add(item)

    class _Repository:
        def __init__(self, session: _Session) -> None:
            self._session = session
            self.dataset_value = SimpleNamespace(
                id=dataset_id,
                checksum="d" * 64,
                feature_set_version_id=feature_set_version_id,
            )
            self.experiment_value = SimpleNamespace(
                id=experiment_id,
                dataset_snapshot_id=dataset_id,
                feature_set_version_id=feature_set_version_id,
                input_checksum="e" * 64,
            )
            self.rows = [
                SimpleNamespace(
                    id=uuid4(),
                    fixture_id=fixture_ids[0],
                    feature_id="home_form",
                    numeric_value=Decimal("2"),
                ),
                SimpleNamespace(
                    id=uuid4(),
                    fixture_id=fixture_ids[1],
                    feature_id="home_form",
                    numeric_value=Decimal("1"),
                ),
            ]
            self.calibrations_by_key: dict[str, object] = {}
            self.calibrations_by_version: dict[tuple[str, str], object] = {}
            self.calibrations_by_id: dict[UUID, object] = {}
            self.runs_by_key: dict[str, object] = {}
            self.runs_by_code: dict[str, object] = {}
            self.evaluations_by_key: dict[str, object] = {}
            self.evaluations_by_code: dict[tuple[UUID, str], object] = {}

        async def dataset(self, identifier: UUID) -> object | None:
            return self.dataset_value if identifier == dataset_id else None

        async def experiment(self, identifier: UUID) -> object | None:
            return self.experiment_value if identifier == experiment_id else None

        async def dataset_rows(self, identifier: UUID) -> list[object]:
            return self.rows if identifier == dataset_id else []

        async def calibration(self, identifier: UUID) -> object | None:
            return self.calibrations_by_id.get(identifier)

        async def existing_calibration(self, key: str) -> object | None:
            return self.calibrations_by_key.get(key)

        async def calibration_by_code_version(self, code: str, version: str) -> object | None:
            return self.calibrations_by_version.get((code, version))

        async def create_calibration(self, calibration: object) -> object:
            calibration.id = uuid4()
            self._session.add(calibration)
            self.calibrations_by_key[calibration.idempotency_key] = calibration
            self.calibrations_by_version[(calibration.calibration_code, calibration.version)] = (
                calibration
            )
            self.calibrations_by_id[calibration.id] = calibration
            return calibration

        async def existing_run(self, key: str) -> object | None:
            return self.runs_by_key.get(key)

        async def run_by_code(self, code: str) -> object | None:
            return self.runs_by_code.get(code)

        async def create_run(self, run: object) -> object:
            run.id = uuid4()
            self._session.add(run)
            self.runs_by_key[run.idempotency_key] = run
            self.runs_by_code[run.run_code] = run
            return run

        async def run(self, identifier: UUID) -> object | None:
            return next((run for run in self.runs_by_code.values() if run.id == identifier), None)

        async def outputs_by_ids(self, output_ids: list[UUID]) -> list[object]:
            return [
                item
                for item in self._session.added
                if getattr(item, "id", None) in output_ids
                and item.__class__.__name__ == "ProbabilityOutput"
            ]

        async def existing_evaluation(self, key: str) -> object | None:
            return self.evaluations_by_key.get(key)

        async def evaluation_by_code(self, run_id: UUID, code: str) -> object | None:
            return self.evaluations_by_code.get((run_id, code))

        async def create_evaluation(self, evaluation: object) -> object:
            evaluation.id = uuid4()
            self._session.add(evaluation)
            self.evaluations_by_key[evaluation.idempotency_key] = evaluation
            self.evaluations_by_code[
                (evaluation.probability_run_id, evaluation.evaluation_code)
            ] = evaluation
            return evaluation

    async def run() -> None:
        session = _Session()
        service = ProbabilityService(session)  # type: ignore[arg-type]
        service._repository = _Repository(session)  # type: ignore[assignment]
        calibration = await service.create_calibration(
            CalibrationVersionCreate(
                calibration_code="platt_home_form",
                version="1.0.0",
                method=CalibrationMethod.PLATT,
                parameters={"a": 1.0, "b": 0.0},
                compatible_model_identifiers=["logistic_baseline"],
                owner="research",
            )
        )
        request = ProbabilityRunCreate(
            run_code="home_form_v1",
            dataset_snapshot_id=dataset_id,
            feature_set_version_id=feature_set_version_id,
            research_experiment_id=experiment_id,
            model_identifier="logistic_baseline",
            model_version="1.0.0",
            calibration_version_id=calibration.id,
            market_type="match_result",
            outcome="home_win",
            parameters={"weights": {"home_form": 0.5}, "intercept": 0},
            random_seed=7,
            prediction_timestamp=now,
        )
        first = await service.create_run(request)
        retried = await service.create_run(request)

        assert first.id == retried.id
        assert first.status is ProbabilityRunStatus.COMPLETED
        outputs = [item for item in session.added if item.__class__.__name__ == "ProbabilityOutput"]
        assert len(outputs) == 2
        assert all(0 <= item.estimated_probability <= 1 for item in outputs)
        assert any(item.__class__.__name__ == "ProbabilityLineage" for item in session.added)
        assert any(
            item.__class__.__name__ == "ProbabilityValidationRecord" for item in session.added
        )

        evaluation = await service.create_evaluation(
            first.id,
            ProbabilityEvaluationCreate(
                evaluation_code="settled_fixture_set",
                samples=[
                    EvaluationSample(probability_output_id=outputs[0].id, observed_outcome=True),
                    EvaluationSample(probability_output_id=outputs[1].id, observed_outcome=False),
                ],
            ),
        )
        assert evaluation.sample_count == 2
        assert "brier_score" in evaluation.metrics

        invalid = await service.create_run(
            request.model_copy(
                update={
                    "run_code": "missing_feature_v1",
                    "parameters": {"weights": {"missing_feature": 1.0}},
                }
            )
        )
        assert invalid.status is ProbabilityRunStatus.VALIDATION_FAILED

        with pytest.raises(ProbabilityVersionConflictError):
            await service.create_run(
                request.model_copy(update={"parameters": {"weights": {"home_form": 1.0}}})
            )

    asyncio.run(run())
