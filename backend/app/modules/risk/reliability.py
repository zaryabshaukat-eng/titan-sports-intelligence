from typing import cast

from app.modules.risk.engines import AnalyzerMetadata, RiskContext


class AgreementRiskAnalyzer:
    metadata = AnalyzerMetadata("agreement_risk", "Risk from low model agreement.")

    def assess(self, context: RiskContext, parameters: dict[str, object]) -> float:
        _ = parameters
        return min(
            1.0,
            float(cast(str | float, context.disagreement_metrics.get("standard_deviation", 0)))
            / 0.5,
        )
