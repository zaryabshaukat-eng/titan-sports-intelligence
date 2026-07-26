"""Versioned deterministic probability calibration implementations."""

from __future__ import annotations

from math import exp, log

from app.modules.probability.enums import CalibrationMethod
from app.modules.probability.exceptions import ProbabilityValidationError


def validate_calibration_parameters(
    method: CalibrationMethod, parameters: dict[str, object]
) -> None:
    """Reject ambiguous or invalid calibration configurations before immutable persistence."""
    if method is CalibrationMethod.PLATT:
        coefficient = _number(parameters.get("a"), "parameters.a")
        _number(parameters.get("b"), "parameters.b")
        if coefficient <= 0:
            raise ProbabilityValidationError("Platt calibration requires a positive coefficient.")
        return
    if method is CalibrationMethod.TEMPERATURE:
        temperature = _number(parameters.get("temperature"), "parameters.temperature")
        if temperature <= 0:
            raise ProbabilityValidationError("Temperature calibration requires temperature > 0.")
        return
    points = parameters.get("points")
    if not isinstance(points, list) or len(points) < 2:
        raise ProbabilityValidationError("Isotonic calibration requires at least two points.")
    previous_prediction = -1.0
    previous_calibrated = -1.0
    for point in points:
        if not isinstance(point, dict):
            raise ProbabilityValidationError("Isotonic calibration points must be objects.")
        prediction = _probability(point.get("prediction"), "point.prediction")
        calibrated = _probability(point.get("calibrated"), "point.calibrated")
        if prediction <= previous_prediction or calibrated < previous_calibrated:
            raise ProbabilityValidationError(
                "Isotonic points must increase by prediction and not decrease calibrated."
            )
        previous_prediction = prediction
        previous_calibrated = calibrated


def calibrate(
    probability: float, *, method: CalibrationMethod, parameters: dict[str, object]
) -> float:
    """Calibrate one raw probability with a fully persisted versioned configuration."""
    validate_calibration_parameters(method, parameters)
    bounded = _clamp(probability)
    if method is CalibrationMethod.PLATT:
        logit = _logit(bounded)
        coefficient = _number(parameters["a"], "parameters.a")
        intercept = _number(parameters["b"], "parameters.b")
        return _sigmoid((coefficient * logit) + intercept)
    if method is CalibrationMethod.TEMPERATURE:
        temperature = _number(parameters["temperature"], "parameters.temperature")
        return _sigmoid(_logit(bounded) / temperature)
    return _isotonic(bounded, parameters["points"])


def _isotonic(probability: float, points: object) -> float:
    """Linearly interpolate validated isotonic points with endpoint clipping."""
    assert isinstance(points, list)
    parsed = [
        (
            _probability(point["prediction"], "point.prediction"),
            _probability(point["calibrated"], "point.calibrated"),
        )
        for point in points
        if isinstance(point, dict)
    ]
    if probability <= parsed[0][0]:
        return parsed[0][1]
    if probability >= parsed[-1][0]:
        return parsed[-1][1]
    for (left_x, left_y), (right_x, right_y) in zip(parsed, parsed[1:], strict=True):
        if left_x <= probability <= right_x:
            ratio = (probability - left_x) / (right_x - left_x)
            return left_y + (ratio * (right_y - left_y))
    raise AssertionError("validated isotonic points did not cover the probability")


def _number(value: object, field: str) -> float:
    if not isinstance(value, int | float):
        raise ProbabilityValidationError(f"{field} must be numeric.")
    return float(value)


def _probability(value: object, field: str) -> float:
    parsed = _number(value, field)
    if not 0 <= parsed <= 1:
        raise ProbabilityValidationError(f"{field} must be between 0 and 1.")
    return parsed


def _clamp(value: float) -> float:
    return min(1 - 1e-12, max(1e-12, value))


def _logit(value: float) -> float:
    bounded = _clamp(value)
    return log(bounded / (1 - bounded))


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + exp(-value))
    exponent = exp(value)
    return exponent / (1 + exponent)
