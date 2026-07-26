from app.modules.risk.engines import AnalyzerMetadata, RiskContext


class StabilityAnalyzer:
    metadata = AnalyzerMetadata(
        "stability", "Risk from probability disagreement and pairwise divergence."
    )

    def assess(self, context: RiskContext, parameters: dict[str, object]) -> float:
        _ = parameters
        return min(1.0, float(context.disagreement_metrics.get("mean_pairwise_divergence", 0)) * 2)
