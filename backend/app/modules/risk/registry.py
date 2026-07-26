from app.modules.risk.calibration import CalibrationRiskAnalyzer
from app.modules.risk.data_quality import DataQualityAnalyzer
from app.modules.risk.engines import RiskAnalyzer
from app.modules.risk.reliability import AgreementRiskAnalyzer
from app.modules.risk.stability import StabilityAnalyzer
from app.modules.risk.uncertainty import UncertaintyAnalyzer


class RiskAnalyzerRegistry:
    def __init__(self, analyzers: tuple[RiskAnalyzer, ...] | None = None) -> None:
        items = analyzers or (
            UncertaintyAnalyzer(),
            StabilityAnalyzer(),
            CalibrationRiskAnalyzer(),
            AgreementRiskAnalyzer(),
            DataQualityAnalyzer(),
        )
        self._items = {item.metadata.identifier: item for item in items}

    def analyzers(self) -> list[RiskAnalyzer]:
        return [self._items[key] for key in sorted(self._items)]
