from dataclasses import dataclass
from typing import Protocol, cast


@dataclass(frozen=True, slots=True)
class ScenarioMetadata:
    identifier: str
    description: str


class Scenario(Protocol):
    """A type-preserving chronological selection strategy."""

    metadata: ScenarioMetadata

    def select[T](self, items: list[T], parameters: dict[str, object]) -> list[T]: ...


class HistoricalReplay:
    metadata = ScenarioMetadata(
        "historical_replay", "Chronological replay of all eligible historical observations."
    )

    def select[T](self, items: list[T], parameters: dict[str, object]) -> list[T]:
        _ = parameters
        return items


class RollingWindow:
    metadata = ScenarioMetadata("rolling_window", "Most recent fixed historical window.")

    def select[T](self, items: list[T], parameters: dict[str, object]) -> list[T]:
        return items[-int(cast(int, parameters.get("window_size", len(items)))) :]


class ExpandingWindow:
    metadata = ScenarioMetadata("expanding_window", "Chronological expanding-history interface.")

    def select[T](self, items: list[T], parameters: dict[str, object]) -> list[T]:
        _ = parameters
        return items


class WalkForward:
    metadata = ScenarioMetadata("walk_forward", "Chronological walk-forward interface.")

    def select[T](self, items: list[T], parameters: dict[str, object]) -> list[T]:
        _ = parameters
        return items


class TimeSplit:
    metadata = ScenarioMetadata("time_split", "Final chronological holdout split.")

    def select[T](self, items: list[T], parameters: dict[str, object]) -> list[T]:
        ratio = float(cast(int | float, parameters.get("test_fraction", 0.2)))
        return items[max(0, int(len(items) * (1 - ratio))) :]
