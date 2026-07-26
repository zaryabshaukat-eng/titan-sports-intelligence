"""Registry that decouples Probability Engine business flow from model implementations."""

from __future__ import annotations

from app.modules.probability.engines import (
    BayesianBaselineModel,
    EloBaselineModel,
    LogisticBaselineModel,
    ModelMetadata,
    PoissonBaselineModel,
    ProbabilityModel,
)
from app.modules.probability.exceptions import ProbabilityResolutionError


class ProbabilityModelRegistry:
    """Resolve reviewed versioned models without hard-coding them into services or APIs."""

    def __init__(self, models: tuple[ProbabilityModel, ...] | None = None) -> None:
        registered = models or (
            LogisticBaselineModel(),
            PoissonBaselineModel(),
            EloBaselineModel(),
            BayesianBaselineModel(),
        )
        self._models = {
            (model.metadata.model_identifier, model.metadata.version): model for model in registered
        }

    def resolve(self, identifier: str, version: str) -> ProbabilityModel:
        """Return exactly the requested model implementation or a controlled resolution error."""
        model = self._models.get((identifier, version))
        if model is None:
            raise ProbabilityResolutionError("Probability model identifier/version was not found.")
        return model

    def metadata(self) -> list[ModelMetadata]:
        """Return stable model metadata for protected discovery APIs."""
        return [self._models[key].metadata for key in sorted(self._models)]
