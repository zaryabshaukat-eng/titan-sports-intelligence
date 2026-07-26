"""Explicit Research Engine failures translated only at the API boundary."""


class ResearchError(Exception):
    """Base error for the Research bounded context."""


class DatasetResolutionError(ResearchError):
    """Raised when a requested Feature Set version or dataset snapshot cannot be resolved."""


class DatasetVersionConflictError(ResearchError):
    """Raised when an immutable dataset code/version is requested with different source inputs."""


class ExperimentVersionConflictError(ResearchError):
    """Raised when a stable experiment code would describe different immutable inputs."""


class ResearchValidationError(ResearchError):
    """Raised before an experiment can be materialized from invalid research configuration."""
