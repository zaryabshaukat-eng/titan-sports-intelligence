from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScenarioMetadata:
    identifier: str
    description: str


class HistoricalReplay:
    metadata = ScenarioMetadata(
        "historical_replay", "Chronological replay of all eligible historical observations."
    )

    def select(self, items: list[object], parameters: dict[str, object]) -> list[object]:
        _ = parameters
        return items


class RollingWindow:
    metadata = ScenarioMetadata("rolling_window", "Most recent fixed historical window.")

    def select(self, items: list[object], parameters: dict[str, object]) -> list[object]:
        return items[-int(parameters.get("window_size", len(items))) :]


class ExpandingWindow:
    metadata = ScenarioMetadata("expanding_window", "Chronological expanding-history interface.")

    def select(self, items: list[object], parameters: dict[str, object]) -> list[object]:
        _ = parameters
        return items


class WalkForward:
    metadata = ScenarioMetadata("walk_forward", "Chronological walk-forward interface.")

    def select(self, items: list[object], parameters: dict[str, object]) -> list[object]:
        _ = parameters
        return items


class TimeSplit:
    metadata = ScenarioMetadata("time_split", "Final chronological holdout split.")

    def select(self, items: list[object], parameters: dict[str, object]) -> list[object]:
        ratio = float(parameters.get("test_fraction", 0.2))
        return items[max(0, int(len(items) * (1 - ratio))) :]
