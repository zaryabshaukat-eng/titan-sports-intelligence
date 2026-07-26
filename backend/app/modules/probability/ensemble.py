"""Configurable deterministic ensemble calculations; weights are never auto-optimized here."""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.probability.exceptions import ProbabilityValidationError


@dataclass(frozen=True, slots=True)
class EnsembleMember:
    """A named immutable model output with an explicitly configured weight."""

    model_identifier: str
    probability: float
    weight: float


def weighted_probability(members: list[EnsembleMember]) -> float:
    """Combine independent model estimates using declared positive weights only."""
    if not members:
        raise ProbabilityValidationError("An ensemble requires at least one member.")
    if len({member.model_identifier for member in members}) != len(members):
        raise ProbabilityValidationError("An ensemble cannot contain duplicate model identifiers.")
    if any(member.weight <= 0 for member in members):
        raise ProbabilityValidationError("Ensemble weights must be positive.")
    if any(not 0 <= member.probability <= 1 for member in members):
        raise ProbabilityValidationError("Ensemble probabilities must be between 0 and 1.")
    total_weight = sum(member.weight for member in members)
    return sum(member.probability * member.weight for member in members) / total_weight
