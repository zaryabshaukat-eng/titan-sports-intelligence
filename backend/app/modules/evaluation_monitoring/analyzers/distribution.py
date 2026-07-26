from __future__ import annotations

from math import log, sqrt

EPSILON = 1e-12


def normalize(values: list[float]) -> list[float]:
    total = sum(max(0.0, value) for value in values)
    return [max(0.0, value) / total for value in values] if total else [0.0] * len(values)


def psi(baseline: list[float], current: list[float]) -> float:
    return sum(
        (c - b) * log((c + EPSILON) / (b + EPSILON)) for b, c in zip(baseline, current, strict=True)
    )


def kl(baseline: list[float], current: list[float]) -> float:
    return sum(
        b * log((b + EPSILON) / (c + EPSILON)) for b, c in zip(baseline, current, strict=True)
    )


def js(baseline: list[float], current: list[float]) -> float:
    midpoint = [(b + c) / 2 for b, c in zip(baseline, current, strict=True)]
    return (kl(baseline, midpoint) + kl(current, midpoint)) / 2


def wasserstein(baseline: list[float], current: list[float]) -> float:
    cumulative_b = cumulative_c = distance = 0.0
    for b, c in zip(baseline, current, strict=True):
        cumulative_b += b
        cumulative_c += c
        distance += abs(cumulative_b - cumulative_c)
    return distance / max(1, len(baseline) - 1)


def l2(baseline: list[float], current: list[float]) -> float:
    return sqrt(sum((b - c) ** 2 for b, c in zip(baseline, current, strict=True)))
