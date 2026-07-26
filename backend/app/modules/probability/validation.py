"""Explicit reproducibility and compatibility validation for Probability Engine runs."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.probability.engines import ProbabilityModel
from app.modules.probability.enums import ProbabilityValidationStatus
from app.modules.probability.inference import FixtureFeatureVector
from app.modules.probability.models import CalibrationVersion
from app.modules.research.models import DatasetSnapshot, ResearchExperiment


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """One durable evidence record that explains a run's eligibility or failure."""

    rule_name: str
    status: ProbabilityValidationStatus
    message: str


def validate_run(
    *,
    dataset: DatasetSnapshot,
    requested_feature_set_version_id: UUID,
    experiment: ResearchExperiment,
    model: ProbabilityModel,
    parameters: dict[str, object],
    vectors: list[FixtureFeatureVector],
    calibration: CalibrationVersion | None,
) -> tuple[ValidationFinding, ...]:
    """Verify frozen-data, model, and calibration compatibility before canonical outputs exist."""
    findings = [
        _finding(
            "feature_set_version",
            dataset.feature_set_version_id == requested_feature_set_version_id,
            "dataset and requested run reference the same Feature Set version",
            "dataset snapshot and requested run reference different Feature Set versions",
        ),
        _finding(
            "research_experiment",
            experiment.dataset_snapshot_id == dataset.id
            and experiment.feature_set_version_id == requested_feature_set_version_id,
            "research experiment traces to this dataset and Feature Set version",
            "research experiment does not trace to this dataset and Feature Set version",
        ),
        _finding(
            "fixture_vectors",
            bool(vectors),
            "dataset contains numeric fixture-scoped values for inference",
            "dataset contains no numeric fixture-scoped values for inference",
        ),
    ]
    try:
        required_features = model.required_features(parameters)
        compatible = bool(vectors) and all(
            required_features.issubset(vector.features) for vector in vectors
        )
        findings.append(
            _finding(
                "model_feature_compatibility",
                compatible,
                "all fixture vectors contain the model's declared required features",
                "one or more fixture vectors lack a model-required feature",
            )
        )
        if compatible:
            model.infer(
                features=vectors[0].features,
                parameters=parameters,
                random_seed=0,
            )
            findings.append(
                _finding(
                    "model_parameters",
                    True,
                    "model parameters are valid for the requested baseline",
                    "",
                )
            )
    except ValueError as exc:
        findings.append(
            _finding("model_parameters", False, "", f"model parameters are invalid: {exc}")
        )
    calibration_compatible = calibration is None or (
        not calibration.compatible_model_identifiers
        or model.metadata.model_identifier in calibration.compatible_model_identifiers
    )
    findings.append(
        _finding(
            "calibration_compatibility",
            calibration_compatible,
            "calibration is compatible with the selected model",
            "calibration is not declared compatible with the selected model",
        )
    )
    return tuple(findings)


def _finding(
    rule_name: str, passed: bool, passed_message: str, failed_message: str
) -> ValidationFinding:
    return ValidationFinding(
        rule_name=rule_name,
        status=ProbabilityValidationStatus.PASSED if passed else ProbabilityValidationStatus.FAILED,
        message=passed_message if passed else failed_message,
    )
