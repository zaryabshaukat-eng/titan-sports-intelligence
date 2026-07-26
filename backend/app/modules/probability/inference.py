"""Frozen-dataset feature-vector construction and deterministic inference helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import sqrt
from uuid import UUID

from app.modules.probability.engines import ProbabilityModel, RawProbability
from app.modules.research.models import DatasetSnapshotRow


@dataclass(frozen=True, slots=True)
class FixtureFeatureVector:
    """One fixture's numeric values extracted solely from a frozen dataset snapshot."""

    fixture_id: UUID
    features: dict[str, float]
    support_count: int


def fixture_feature_vectors(rows: list[DatasetSnapshotRow]) -> list[FixtureFeatureVector]:
    """Aggregate deterministic numeric feature means by canonical fixture identity."""
    values: dict[UUID, dict[str, list[float]]] = {}
    for row in rows:
        if row.fixture_id is None or row.numeric_value is None:
            continue
        fixture_values = values.setdefault(row.fixture_id, {})
        fixture_values.setdefault(row.feature_id, []).append(float(Decimal(str(row.numeric_value))))
    return [
        FixtureFeatureVector(
            fixture_id=fixture_id,
            features={
                feature_id: sum(observations) / len(observations)
                for feature_id, observations in sorted(features.items())
            },
            support_count=sum(len(observations) for observations in features.values()),
        )
        for fixture_id, features in sorted(values.items(), key=lambda item: str(item[0]))
    ]


def infer_fixture_probability(
    *,
    model: ProbabilityModel,
    vector: FixtureFeatureVector,
    parameters: dict[str, object],
    random_seed: int,
) -> tuple[RawProbability, float, float]:
    """Infer one estimate and a deterministic normal-approximation confidence interval."""
    raw = model.infer(
        features=vector.features,
        parameters=parameters,
        random_seed=random_seed,
    )
    support = max(1, vector.support_count, raw.support_count)
    margin = 1.96 * sqrt(raw.probability * (1 - raw.probability) / support)
    return raw, max(0.0, raw.probability - margin), min(1.0, raw.probability + margin)
