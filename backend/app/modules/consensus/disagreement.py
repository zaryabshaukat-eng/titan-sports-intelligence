"""Deterministic disagreement metrics for evidence interpretation."""

from math import log2, sqrt


def metrics(probabilities: list[float]) -> dict[str, float]:
    if not probabilities:
        raise ValueError("Disagreement requires probabilities")
    average = sum(probabilities) / len(probabilities)
    variance = sum((value - average) ** 2 for value in probabilities) / len(probabilities)
    pairwise = [
        abs(left - right)
        for position, left in enumerate(probabilities)
        for right in probabilities[position + 1 :]
    ]
    entropy = sum(_binary_entropy(value) for value in probabilities) / len(probabilities)
    return {
        "standard_deviation": sqrt(variance),
        "max_min_spread": max(probabilities) - min(probabilities),
        "mean_pairwise_divergence": sum(pairwise) / len(pairwise) if pairwise else 0.0,
        "mean_binary_entropy": entropy,
    }


def _binary_entropy(value: float) -> float:
    if value in {0, 1}:
        return 0.0
    return -((value * log2(value)) + ((1 - value) * log2(1 - value)))
