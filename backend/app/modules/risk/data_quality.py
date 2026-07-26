from app.modules.risk.engines import AnalyzerMetadata, RiskContext


class DataQualityAnalyzer:
    metadata = AnalyzerMetadata(
        "data_quality_risk", "Risk from incomplete contributing Probability outputs."
    )

    def assess(self, context: RiskContext, parameters: dict[str, object]) -> float:
        _ = parameters
        return 1 - (context.contributor_count / context.expected_count)
