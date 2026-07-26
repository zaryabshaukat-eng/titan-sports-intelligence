"""Inference model protocol and deterministic baseline implementations."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Static registry contract for an interchangeable inference implementation."""

    model_identifier: str
    version: str
    algorithm: str
    description: str
    parameter_schema: dict[str, object]


@dataclass(frozen=True, slots=True)
class RawProbability:
    """Uncalibrated deterministic model estimate and its support count."""

    probability: float
    support_count: int


class ProbabilityModel(Protocol):
    """Model implementations consume one frozen fixture vector and emit no policy advice."""

    metadata: ModelMetadata

    def required_features(self, parameters: dict[str, object]) -> set[str]:
        """Return feature IDs that must exist in every vector before inference."""

    def infer(
        self, *, features: dict[str, float], parameters: dict[str, object], random_seed: int
    ) -> RawProbability:
        """Calculate a deterministic uncalibrated probability from immutable numeric features."""


def _sigmoid(value: float) -> float:
    """Stable enough logistic transform for bounded baseline inference inputs."""
    if value >= 0:
        return 1 / (1 + exp(-value))
    exponent = exp(value)
    return exponent / (1 + exponent)


def _weights(parameters: dict[str, object]) -> dict[str, float]:
    """Parse a reviewed feature-weight mapping without accepting implicit feature selection."""
    values = parameters.get("weights")
    if not isinstance(values, dict) or not values:
        raise ValueError("parameters.weights must be a non-empty object")
    weights: dict[str, float] = {}
    for feature_id, raw_weight in values.items():
        if not isinstance(feature_id, str) or not feature_id:
            raise ValueError("parameters.weights keys must be non-empty feature IDs")
        if not isinstance(raw_weight, int | float):
            raise ValueError("parameters.weights values must be numeric")
        weights[feature_id] = float(raw_weight)
    return weights


class LogisticBaselineModel:
    """A transparent weighted logistic baseline, ready to be replaced by trained adapters."""

    metadata = ModelMetadata(
        "logistic_baseline",
        "1.0.0",
        "weighted_logistic_baseline",
        "Deterministic logistic transform of explicitly supplied immutable feature weights.",
        {"weights": "object[str, number]", "intercept": "number (optional)"},
    )

    def required_features(self, parameters: dict[str, object]) -> set[str]:
        return set(_weights(parameters))

    def infer(
        self, *, features: dict[str, float], parameters: dict[str, object], random_seed: int
    ) -> RawProbability:
        _ = random_seed
        weights = _weights(parameters)
        intercept = _number(parameters.get("intercept", 0), "parameters.intercept")
        score = intercept + sum(weights[key] * features[key] for key in sorted(weights))
        return RawProbability(_sigmoid(score), len(weights))


class PoissonBaselineModel:
    """A simple event-occurrence Poisson baseline using a declared non-negative rate feature."""

    metadata = ModelMetadata(
        "poisson_baseline",
        "1.0.0",
        "poisson_event_baseline",
        "Transforms a declared rate feature into P(X >= 1) under a Poisson baseline.",
        {"rate_feature": "string", "rate_scale": "number (optional)", "intercept": "number"},
    )

    def required_features(self, parameters: dict[str, object]) -> set[str]:
        feature = parameters.get("rate_feature")
        if not isinstance(feature, str) or not feature:
            raise ValueError("parameters.rate_feature must be a non-empty feature ID")
        return {feature}

    def infer(
        self, *, features: dict[str, float], parameters: dict[str, object], random_seed: int
    ) -> RawProbability:
        _ = random_seed
        feature_id = next(iter(self.required_features(parameters)))
        scale = _number(parameters.get("rate_scale", 1), "parameters.rate_scale")
        intercept = _number(parameters.get("intercept", 0), "parameters.intercept")
        rate = max(0.000001, intercept + (features[feature_id] * scale))
        return RawProbability(1 - exp(-rate), 1)


class EloBaselineModel:
    """A transparent Elo-style comparison baseline over explicitly named rating features."""

    metadata = ModelMetadata(
        "elo_baseline",
        "1.0.0",
        "elo_rating_baseline",
        "Logistic conversion of declared home/away canonical rating feature differences.",
        {
            "home_rating_feature": "string",
            "away_rating_feature": "string",
            "home_advantage": "number (optional)",
            "scale": "number (optional, > 0)",
        },
    )

    def required_features(self, parameters: dict[str, object]) -> set[str]:
        home = parameters.get("home_rating_feature")
        away = parameters.get("away_rating_feature")
        if not isinstance(home, str) or not home or not isinstance(away, str) or not away:
            raise ValueError("parameters.home_rating_feature and away_rating_feature are required")
        if home == away:
            raise ValueError("Elo home and away rating features must differ")
        return {home, away}

    def infer(
        self, *, features: dict[str, float], parameters: dict[str, object], random_seed: int
    ) -> RawProbability:
        _ = random_seed
        home = str(parameters["home_rating_feature"])
        away = str(parameters["away_rating_feature"])
        scale = _number(parameters.get("scale", 400), "parameters.scale")
        if scale <= 0:
            raise ValueError("parameters.scale must be greater than zero")
        advantage = _number(parameters.get("home_advantage", 0), "parameters.home_advantage")
        return RawProbability(_sigmoid((features[home] - features[away] + advantage) / scale), 2)


class BayesianBaselineModel:
    """A beta-prior baseline that can add a declared immutable evidence feature."""

    metadata = ModelMetadata(
        "bayesian_baseline",
        "1.0.0",
        "beta_prior_baseline",
        "A transparent beta-prior probability with optional canonical evidence contribution.",
        {
            "alpha": "number (> 0)",
            "beta": "number (> 0)",
            "evidence_feature": "string (optional)",
        },
    )

    def required_features(self, parameters: dict[str, object]) -> set[str]:
        feature = parameters.get("evidence_feature")
        if feature is None:
            return set()
        if not isinstance(feature, str) or not feature:
            raise ValueError("parameters.evidence_feature must be a non-empty feature ID")
        return {feature}

    def infer(
        self, *, features: dict[str, float], parameters: dict[str, object], random_seed: int
    ) -> RawProbability:
        _ = random_seed
        alpha = _number(parameters.get("alpha"), "parameters.alpha")
        beta = _number(parameters.get("beta"), "parameters.beta")
        if alpha <= 0 or beta <= 0:
            raise ValueError("parameters.alpha and parameters.beta must be greater than zero")
        evidence_feature = self.required_features(parameters)
        evidence = max(0.0, features[next(iter(evidence_feature))]) if evidence_feature else 0.0
        probability = (alpha + evidence) / (alpha + beta + max(1.0, evidence))
        return RawProbability(_clamp_probability(probability), 1 if evidence_feature else 0)


def _number(value: object, field: str) -> float:
    """Validate numeric model parameters before the controlled application-service boundary."""
    if not isinstance(value, int | float):
        raise ValueError(f"{field} must be numeric")
    return float(value)


def _clamp_probability(value: float) -> float:
    """Keep floating-point baseline output inside the formal probability domain."""
    return min(1.0, max(0.0, value))
