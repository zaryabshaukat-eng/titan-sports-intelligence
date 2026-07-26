"""Controlled Consensus Engine errors."""


class ConsensusError(Exception):
    """Base Consensus Engine error."""


class ConsensusResolutionError(ConsensusError):
    """A required Probability artifact or strategy is absent."""


class ConsensusVersionConflictError(ConsensusError):
    """A retry attempts to alter an immutable consensus artifact."""


class ConsensusValidationError(ConsensusError):
    """Consensus inputs or parameters are incompatible."""
