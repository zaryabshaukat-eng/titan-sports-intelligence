"""Explicit consensus weighting helpers."""

from app.modules.consensus.engines import ConsensusEstimate, WeightedAverage


def weighted_average(estimates: list[ConsensusEstimate], weights: dict[str, object]) -> float:
    """Expose weighted calculation independently for transparent testing and review."""
    return WeightedAverage().combine(estimates, {"weights": weights})
