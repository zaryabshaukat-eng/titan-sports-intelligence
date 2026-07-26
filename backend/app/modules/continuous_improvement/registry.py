from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Analyzer:
    identifier: str
    recommendation_type: str
    description: str


class ImprovementAnalyzerRegistry:
    def analyzers(self):
        return [
            Analyzer(
                "drift",
                "research_priority",
                "Prioritize investigation when sustained drift evidence exists.",
            ),
            Analyzer(
                "calibration",
                "calibration_replacement",
                "Review calibration when error evidence degrades.",
            ),
            Analyzer(
                "provider",
                "feature_redesign",
                "Review feature dependencies when provider quality degrades.",
            ),
        ]
