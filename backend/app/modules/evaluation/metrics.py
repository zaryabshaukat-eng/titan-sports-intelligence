from math import sqrt

from app.modules.probability.evaluation import evaluate


def calculate(rows: list[object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Calculate immutable replay metrics without depending on live state.

    The shared probability evaluator supplies the proper scores and calibration
    curve.  Backtests additionally record threshold accuracy, result coverage,
    and dispersion-based stability so comparisons have a complete, stable
    baseline without turning this context into a recommendation engine.
    """
    samples = [(float(item.predicted_probability), item.observed_outcome) for item in rows]
    metrics, reliability = evaluate(samples, bins=10)
    probabilities = [probability for probability, _ in samples]
    mean = sum(probabilities) / len(probabilities)
    variance = sum((probability - mean) ** 2 for probability in probabilities) / len(probabilities)
    metrics.update(
        {
            "accuracy": sum((probability >= 0.5) is outcome for probability, outcome in samples)
            / len(samples),
            "coverage": len(samples) / len(rows),
            "prediction_stability": max(0.0, 1.0 - (sqrt(variance) / 0.5)),
        }
    )
    return metrics, reliability
