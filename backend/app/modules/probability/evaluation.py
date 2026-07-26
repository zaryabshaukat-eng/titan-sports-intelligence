"""Deterministic probability evaluation metrics over explicitly supplied observed outcomes."""

from __future__ import annotations

from math import log
from typing import TypedDict


class ReliabilityBin(TypedDict):
    """One deterministic calibration bucket with stable numeric fields."""

    lower: float
    upper: float
    count: int
    mean_probability: float
    observed_rate: float


type ProbabilityMetrics = dict[str, float | None]


def evaluate(
    samples: list[tuple[float, bool]], *, bins: int
) -> tuple[ProbabilityMetrics, list[ReliabilityBin]]:
    """Calculate reproducible proper scores, discrimination metrics, sharpness, and reliability."""
    if not samples:
        raise ValueError("At least one evaluation sample is required")
    probabilities = [min(1 - 1e-12, max(1e-12, probability)) for probability, _ in samples]
    outcomes = [1.0 if outcome else 0.0 for _, outcome in samples]
    brier = sum(
        (probability - outcome) ** 2
        for probability, outcome in zip(probabilities, outcomes, strict=True)
    ) / len(samples)
    log_loss = -sum(
        (outcome * log(probability)) + ((1 - outcome) * log(1 - probability))
        for probability, outcome in zip(probabilities, outcomes, strict=True)
    ) / len(samples)
    reliability = reliability_curve(samples, bins=bins)
    calibration_error = sum(
        item["count"] * abs(float(item["mean_probability"]) - float(item["observed_rate"]))
        for item in reliability
    ) / len(samples)
    metrics: ProbabilityMetrics = {
        "brier_score": brier,
        "log_loss": log_loss,
        "calibration_error": calibration_error,
        "roc_auc": roc_auc(samples),
        "pr_auc": pr_auc(samples),
        "sharpness": sum(abs(probability - 0.5) * 2 for probability in probabilities)
        / len(samples),
    }
    return metrics, reliability


def reliability_curve(samples: list[tuple[float, bool]], *, bins: int) -> list[ReliabilityBin]:
    """Return stable equal-width reliability buckets, omitting empty buckets."""
    grouped: list[list[tuple[float, bool]]] = [[] for _ in range(bins)]
    for probability, outcome in samples:
        grouped[min(int(probability * bins), bins - 1)].append((probability, outcome))
    values: list[ReliabilityBin] = []
    for index, group in enumerate(grouped):
        if not group:
            continue
        values.append(
            {
                "lower": index / bins,
                "upper": (index + 1) / bins,
                "count": len(group),
                "mean_probability": sum(value for value, _ in group) / len(group),
                "observed_rate": sum(1.0 if outcome else 0.0 for _, outcome in group) / len(group),
            }
        )
    return values


def roc_auc(samples: list[tuple[float, bool]]) -> float | None:
    """Calculate rank-based ROC AUC with deterministic average ranks for tied scores."""
    positive_count = sum(outcome for _, outcome in samples)
    negative_count = len(samples) - positive_count
    if not positive_count or not negative_count:
        return None
    ordered = sorted(enumerate(samples), key=lambda item: item[1][0])
    ranks = [0.0] * len(samples)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1][0] == ordered[index][1][0]:
            end += 1
        rank = ((index + 1) + end) / 2
        for position in range(index, end):
            ranks[ordered[position][0]] = rank
        index = end
    positive_ranks = sum(rank for rank, (_, outcome) in zip(ranks, samples, strict=True) if outcome)
    return (positive_ranks - (positive_count * (positive_count + 1) / 2)) / (
        positive_count * negative_count
    )


def pr_auc(samples: list[tuple[float, bool]]) -> float | None:
    """Calculate a deterministic step-wise precision/recall area."""
    positives = sum(outcome for _, outcome in samples)
    if not positives:
        return None
    true_positive = 0
    false_positive = 0
    previous_recall = 0.0
    area = 0.0
    for _, outcome in sorted(samples, key=lambda item: item[0], reverse=True):
        if outcome:
            true_positive += 1
        else:
            false_positive += 1
        recall = true_positive / positives
        precision = true_positive / (true_positive + false_positive)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area
