"""Deterministic, dependency-light statistical primitives for exploratory research only."""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, sqrt
from statistics import mean, median, stdev


@dataclass(frozen=True, slots=True)
class StatisticalResult:
    """Provider-neutral analysis result ready for immutable experiment persistence."""

    result_key: str
    method: str
    values: dict[str, object]
    numeric_value: float | None
    sample_size: int
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    p_value: float | None = None


def descriptive(values: list[float], *, feature_id: str) -> StatisticalResult:
    """Compute descriptive moments and a normal-approximation 95% confidence interval."""
    if not values:
        return StatisticalResult(f"descriptive:{feature_id}", "descriptive", {"count": 0}, None, 0)
    average = mean(values)
    deviation = stdev(values) if len(values) > 1 else 0.0
    margin = 1.96 * deviation / sqrt(len(values)) if len(values) > 1 else 0.0
    return StatisticalResult(
        f"descriptive:{feature_id}",
        "descriptive",
        {
            "count": len(values),
            "mean": average,
            "median": median(values),
            "minimum": min(values),
            "maximum": max(values),
            "standard_deviation": deviation,
        },
        average,
        len(values),
        average - margin,
        average + margin,
    )


def correlation(
    left: dict[str, float], right: dict[str, float], *, left_feature: str, right_feature: str
) -> StatisticalResult:
    """Calculate Pearson correlation over deterministic shared canonical-subject keys."""
    keys = sorted(set(left).intersection(right))
    if len(keys) < 2:
        return StatisticalResult(
            f"correlation:{left_feature}:{right_feature}",
            "pearson_correlation",
            {"paired_count": len(keys)},
            None,
            len(keys),
        )
    x_values = [left[key] for key in keys]
    y_values = [right[key] for key in keys]
    x_mean, y_mean = mean(x_values), mean(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=True))
    denominator = sqrt(
        sum((x - x_mean) ** 2 for x in x_values) * sum((y - y_mean) ** 2 for y in y_values)
    )
    coefficient = numerator / denominator if denominator else 0.0
    return StatisticalResult(
        f"correlation:{left_feature}:{right_feature}",
        "pearson_correlation",
        {"paired_count": len(keys), "coefficient": coefficient},
        coefficient,
        len(keys),
    )


def distribution(values: list[float], *, feature_id: str, bins: int) -> StatisticalResult:
    """Create a deterministic equal-width histogram with no predictive interpretation."""
    if not values:
        return StatisticalResult(
            f"distribution:{feature_id}", "equal_width_histogram", {"bins": []}, None, 0
        )
    low, high = min(values), max(values)
    if low == high:
        histogram = [{"lower": low, "upper": high, "count": len(values)}]
    else:
        width = (high - low) / bins
        counts = [0] * bins
        for value in values:
            index = min(int((value - low) / width), bins - 1)
            counts[index] += 1
        histogram = [
            {"lower": low + index * width, "upper": low + (index + 1) * width, "count": count}
            for index, count in enumerate(counts)
        ]
    return StatisticalResult(
        f"distribution:{feature_id}",
        "equal_width_histogram",
        {"bins": histogram},
        None,
        len(values),
    )


def welch_significance(
    left: list[float], right: list[float], *, left_feature: str, right_feature: str
) -> StatisticalResult:
    """Use a documented normal approximation for an exploratory two-sample Welch-style test."""
    if len(left) < 2 or len(right) < 2:
        return StatisticalResult(
            f"significance:{left_feature}:{right_feature}",
            "welch_t_normal_approximation",
            {"left_count": len(left), "right_count": len(right)},
            None,
            len(left) + len(right),
        )
    difference = mean(left) - mean(right)
    standard_error = sqrt((stdev(left) ** 2 / len(left)) + (stdev(right) ** 2 / len(right)))
    statistic = difference / standard_error if standard_error else 0.0
    p_value = 2 * (1 - _normal_cdf(abs(statistic)))
    margin = 1.96 * standard_error
    return StatisticalResult(
        f"significance:{left_feature}:{right_feature}",
        "welch_t_normal_approximation",
        {
            "left_count": len(left),
            "right_count": len(right),
            "mean_difference": difference,
            "t_statistic": statistic,
        },
        statistic,
        len(left) + len(right),
        difference - margin,
        difference + margin,
        p_value,
    )


def _normal_cdf(value: float) -> float:
    """Standard normal CDF used only for the documented exploratory approximation."""
    return 0.5 * (1 + erf(value / sqrt(2)))
