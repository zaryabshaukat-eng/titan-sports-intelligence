from dataclasses import dataclass

from app.modules.evaluation_monitoring.analyzers.distribution import js, kl, psi, wasserstein


@dataclass(frozen=True, slots=True)
class Analyzer:
    identifier: str
    description: str
    calculate: object


class MonitoringAnalyzerRegistry:
    def __init__(self, analyzers: tuple[Analyzer, ...] | None = None) -> None:
        values = analyzers or (
            Analyzer("population_stability_index", "Population Stability Index.", psi),
            Analyzer("kl_divergence", "Kullback-Leibler divergence.", kl),
            Analyzer("jensen_shannon_divergence", "Jensen-Shannon divergence.", js),
            Analyzer("wasserstein_distance", "Distributional Wasserstein distance.", wasserstein),
        )
        self._items = {item.identifier: item for item in values}

    def analyzers(self) -> list[Analyzer]:
        return [self._items[key] for key in sorted(self._items)]
