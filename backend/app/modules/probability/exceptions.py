"""Explicit errors raised at the Probability Engine application boundary."""


class ProbabilityError(Exception):
    """Base class for controlled Probability Engine failures."""


class ProbabilityResolutionError(ProbabilityError):
    """A referenced immutable dataset, experiment, model, or calibration was absent."""


class ProbabilityVersionConflictError(ProbabilityError):
    """An immutable run, calibration, or evaluation version conflicts with prior evidence."""


class ProbabilityValidationError(ProbabilityError):
    """A request or compatibility check fails before inference can be persisted."""
