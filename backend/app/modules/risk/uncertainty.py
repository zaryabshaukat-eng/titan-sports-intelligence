from math import log2
from typing import cast

from app.modules.risk.engines import AnalyzerMetadata, RiskContext


class UncertaintyAnalyzer:
    metadata = AnalyzerMetadata("uncertainty", "Entropy and consensus spread uncertainty.")

    def assess(self, context: RiskContext, parameters: dict[str, object]) -> float:
        _ = parameters
        p = min(1 - 1e-12, max(1e-12, context.consensus_probability))
        entropy = -((p * log2(p)) + ((1 - p) * log2(1 - p)))
        return min(
            1.0,
            (
                entropy
                + float(
                    cast(str | float, context.disagreement_metrics.get("standard_deviation", 0))
                )
                * 2
            )
            / 2,
        )
