"""Evidence-only confidence composition; it intentionally contains no publishing policy."""


def metrics(
    *, disagreement: dict[str, float], calibration_quality: float, completeness: float
) -> tuple[float, dict[str, float], str]:
    agreement = max(0.0, 1 - (disagreement["standard_deviation"] / 0.5))
    calibration = min(1.0, max(0.0, calibration_quality))
    complete = min(1.0, max(0.0, completeness))
    score = (agreement + calibration + complete) / 3
    level = "high" if score >= 0.8 else "medium" if score >= 0.55 else "low"
    return (
        score,
        {
            "model_agreement": agreement,
            "calibration_quality": calibration,
            "input_completeness": complete,
        },
        level,
    )
