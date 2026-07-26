from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RiskContext:
    consensus_probability: float
    confidence_metrics: dict[str, object]
    disagreement_metrics: dict[str, object]
    contributor_count: int
    expected_count: int
    calibration_quality: float


@dataclass(frozen=True, slots=True)
class AnalyzerMetadata:
    identifier: str
    description: str


class RiskAnalyzer(Protocol):
    metadata: AnalyzerMetadata

    def assess(self, context: RiskContext, parameters: dict[str, object]) -> float: ...
