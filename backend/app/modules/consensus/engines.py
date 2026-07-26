"""Pluggable deterministic consensus strategy protocol and implementations."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConsensusEstimate:
    probability_run_id: UUID
    probability: float


@dataclass(frozen=True, slots=True)
class StrategyMetadata:
    identifier: str
    description: str
    parameter_schema: dict[str, object]


class ConsensusStrategyEngine(Protocol):
    metadata: StrategyMetadata

    def combine(
        self, estimates: list[ConsensusEstimate], parameters: dict[str, object]
    ) -> float: ...


def _values(estimates: list[ConsensusEstimate]) -> list[float]:
    if not estimates:
        raise ValueError("Consensus requires at least one estimate")
    if any(not 0 <= item.probability <= 1 for item in estimates):
        raise ValueError("Consensus estimates must be probabilities")
    return [item.probability for item in estimates]


class WeightedAverage:
    metadata = StrategyMetadata(
        "weighted_average",
        "Explicit positive run weights.",
        {"weights": "object[probability_run_id, number]"},
    )

    def combine(self, estimates: list[ConsensusEstimate], parameters: dict[str, object]) -> float:
        _values(estimates)
        raw = parameters.get("weights", {})
        if not isinstance(raw, dict):
            raise ValueError("parameters.weights must be an object")
        weights = [float(raw.get(str(item.probability_run_id), 1.0)) for item in estimates]
        if any(weight <= 0 for weight in weights):
            raise ValueError("Consensus weights must be positive")
        return sum(
            item.probability * weight for item, weight in zip(estimates, weights, strict=True)
        ) / sum(weights)


class Median:
    metadata = StrategyMetadata("median", "Robust median of probability estimates.", {})

    def combine(self, estimates: list[ConsensusEstimate], parameters: dict[str, object]) -> float:
        _ = parameters
        return float(median(_values(estimates)))


class TrimmedMean:
    metadata = StrategyMetadata(
        "trimmed_mean",
        "Symmetrically trims probability extremes.",
        {"trim_fraction": "number in [0, 0.5)"},
    )

    def combine(self, estimates: list[ConsensusEstimate], parameters: dict[str, object]) -> float:
        values = sorted(_values(estimates))
        fraction = float(parameters.get("trim_fraction", 0.1))
        if not 0 <= fraction < 0.5:
            raise ValueError("parameters.trim_fraction must be in [0, 0.5)")
        trim = int(len(values) * fraction)
        kept = values[trim : len(values) - trim] if trim else values
        return sum(kept) / len(kept)


class MajorityVoting:
    metadata = StrategyMetadata(
        "majority_voting",
        "Vote fraction over a declared probability threshold.",
        {"threshold": "number in [0, 1]"},
    )

    def combine(self, estimates: list[ConsensusEstimate], parameters: dict[str, object]) -> float:
        values = _values(estimates)
        threshold = float(parameters.get("threshold", 0.5))
        if not 0 <= threshold <= 1:
            raise ValueError("parameters.threshold must be in [0, 1]")
        return sum(value >= threshold for value in values) / len(values)


class BayesianPooling:
    metadata = StrategyMetadata(
        "bayesian_pooling",
        "Beta-prior pooling framework with fixed reviewed priors.",
        {"alpha": "number > 0", "beta": "number > 0"},
    )

    def combine(self, estimates: list[ConsensusEstimate], parameters: dict[str, object]) -> float:
        values = _values(estimates)
        alpha, beta = float(parameters.get("alpha", 1)), float(parameters.get("beta", 1))
        if alpha <= 0 or beta <= 0:
            raise ValueError("Bayesian pooling alpha and beta must be positive")
        return (alpha + sum(values)) / (alpha + beta + len(values))
