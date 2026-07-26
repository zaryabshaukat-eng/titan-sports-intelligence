from app.modules.evaluation.scenarios import (
    ExpandingWindow,
    HistoricalReplay,
    RollingWindow,
    Scenario,
    ScenarioMetadata,
    TimeSplit,
    WalkForward,
)


class ScenarioRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Scenario] = {
            item.metadata.identifier: item
            for item in (
                HistoricalReplay(),
                RollingWindow(),
                ExpandingWindow(),
                WalkForward(),
                TimeSplit(),
            )
        }

    def resolve(self, id: str) -> Scenario:
        return self._items[id]

    def metadata(self) -> list[ScenarioMetadata]:
        return [self._items[k].metadata for k in sorted(self._items)]
