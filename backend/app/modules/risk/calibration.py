from app.modules.risk.engines import AnalyzerMetadata, RiskContext


class CalibrationRiskAnalyzer:
    metadata = AnalyzerMetadata(
        "calibration_risk", "Risk from available historical calibration quality."
    )

    def assess(self, context: RiskContext, parameters: dict[str, object]) -> float:
        _ = parameters
        return 1 - context.calibration_quality
