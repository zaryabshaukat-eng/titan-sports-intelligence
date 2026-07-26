from app.modules.evaluation.scenarios import (
    ExpandingWindow,
    HistoricalReplay,
    RollingWindow,
    TimeSplit,
    WalkForward,
)


class ScenarioRegistry:
    def __init__(self) -> None:
        self._items = {
            item.metadata.identifier: item
            for item in (
                HistoricalReplay(),
                RollingWindow(),
                ExpandingWindow(),
                WalkForward(),
                TimeSplit(),
            )
        }

    def resolve(self, id: str):
        return self._items[id]

    def metadata(self):
        return [self._items[k].metadata for k in sorted(self._items)]
