from dataclasses import dataclass

from app.modules.explainability.feature_importance import Contribution, deterministic


@dataclass(frozen=True, slots=True)
class ExplainerMetadata:
    identifier: str
    description: str


class DeterministicFeatureExplainer:
    metadata = ExplainerMetadata(
        "deterministic_feature_share",
        "Normalizes immutable numeric feature magnitude into provider-neutral contribution shares.",
    )

    def explain(self, rows: list[object]) -> list[Contribution]:
        return deterministic(rows)
