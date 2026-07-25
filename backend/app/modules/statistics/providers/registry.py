"""Explicit provider registry; adding a provider does not alter business logic."""

from app.modules.statistics.providers.base import StatisticsProviderAdapter
from app.modules.statistics.providers.statistics_feed_v1 import StatisticsFeedV1Adapter


class StatisticsProviderRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, StatisticsProviderAdapter] = {}

    def register(self, adapter: StatisticsProviderAdapter) -> None:
        self._adapters[adapter.provider_name] = adapter

    def get(self, name: str) -> StatisticsProviderAdapter:
        if name not in self._adapters:
            raise KeyError(name)
        return self._adapters[name]


def build_default_registry() -> StatisticsProviderRegistry:
    registry = StatisticsProviderRegistry()
    registry.register(StatisticsFeedV1Adapter())
    return registry
