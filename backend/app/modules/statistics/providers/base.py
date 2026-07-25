"""Provider adapter contract for source-specific statistic feeds."""

from abc import ABC, abstractmethod
from typing import Any

from app.modules.statistics.schemas import NormalizedStatisticsPayload


class StatisticsProviderAdapter(ABC):
    provider_name: str

    @abstractmethod
    def normalize(self, payload: dict[str, Any]) -> NormalizedStatisticsPayload: ...

    @abstractmethod
    def extract_fixture_reference(
        self, payload: dict[str, Any]
    ) -> tuple[str | None, str | None]: ...
