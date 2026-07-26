"""Explicit lineage construction for reproducible research artifacts."""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

from app.modules.research.models import ExperimentLineage


def fingerprint(value: object) -> str:
    """Produce stable checksums for immutable dataset and experiment inputs."""
    payload = json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_experiment_lineage(
    *,
    experiment_id: UUID,
    dataset_snapshot_id: UUID,
    feature_set_version_id: UUID,
    generator_versions: dict[str, str],
    parameters: dict[str, object],
    random_seed: int,
) -> ExperimentLineage:
    """Materialize the version/parameters/seed tuple required for exact replay."""
    return ExperimentLineage(
        experiment_id=experiment_id,
        dataset_snapshot_id=dataset_snapshot_id,
        feature_set_version_id=feature_set_version_id,
        generator_versions=generator_versions,
        parameters_checksum=fingerprint(parameters),
        random_seed=random_seed,
    )
