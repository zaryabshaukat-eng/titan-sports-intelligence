"""Registry decoupling consensus orchestration from specific combination strategies."""

from app.modules.consensus.engines import (
    BayesianPooling,
    ConsensusStrategyEngine,
    MajorityVoting,
    Median,
    StrategyMetadata,
    TrimmedMean,
    WeightedAverage,
)
from app.modules.consensus.exceptions import ConsensusResolutionError


class ConsensusStrategyRegistry:
    def __init__(self, strategies: tuple[ConsensusStrategyEngine, ...] | None = None) -> None:
        registered = strategies or (
            WeightedAverage(),
            Median(),
            TrimmedMean(),
            MajorityVoting(),
            BayesianPooling(),
        )
        self._strategies = {item.metadata.identifier: item for item in registered}

    def resolve(self, identifier: str) -> ConsensusStrategyEngine:
        strategy = self._strategies.get(identifier)
        if strategy is None:
            raise ConsensusResolutionError("Consensus strategy was not found.")
        return strategy

    def metadata(self) -> list[StrategyMetadata]:
        return [self._strategies[key].metadata for key in sorted(self._strategies)]
