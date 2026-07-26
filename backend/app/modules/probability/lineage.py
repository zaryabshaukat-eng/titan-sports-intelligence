"""Checksum and immutable lineage construction for reproducible probability estimates."""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

from app.modules.probability.models import ProbabilityLineage


def fingerprint(value: object) -> str:
    """Generate a canonical SHA-256 fingerprint for replayable configuration inputs."""
    payload = json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_lineage(
    *,
    probability_run_id: UUID,
    dataset_snapshot_id: UUID,
    feature_set_version_id: UUID,
    research_experiment_id: UUID,
    model_identifier: str,
    model_version: str,
    calibration_version: str | None,
    parameters: dict[str, object],
    random_seed: int,
) -> ProbabilityLineage:
    """Materialize the complete immutable lineage path for one probability run."""
    return ProbabilityLineage(
        probability_run_id=probability_run_id,
        dataset_snapshot_id=dataset_snapshot_id,
        feature_set_version_id=feature_set_version_id,
        research_experiment_id=research_experiment_id,
        model_identifier=model_identifier,
        model_version=model_version,
        calibration_version=calibration_version,
        parameters_checksum=fingerprint(parameters),
        random_seed=random_seed,
    )
