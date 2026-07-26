"""Explicit Feature Store domain failures suitable for API-boundary translation."""


class FeatureStoreError(Exception):
    """Base error for this bounded context."""


class FeatureSetVersionConflictError(FeatureStoreError):
    """Raised when a requested immutable version does not match its saved definition checksum."""


class FeatureGenerationResolutionError(FeatureStoreError):
    """Raised when a requested canonical fixture cannot be resolved for generation."""
