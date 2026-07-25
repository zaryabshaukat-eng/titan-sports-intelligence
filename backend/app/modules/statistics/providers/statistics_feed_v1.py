"""Reference adapter; intentionally keeps provider vocabulary at the boundary."""

from typing import Any

from pydantic import BaseModel, Field

from app.modules.statistics.providers.base import StatisticsProviderAdapter
from app.modules.statistics.schemas import NormalizedStatisticsPayload


class StatisticsFeedV1Payload(BaseModel):
    fixture: dict[str, Any]
    observed_at: str
    statistics: list[dict[str, Any]] = Field(min_length=1)


class StatisticsFeedV1Adapter(StatisticsProviderAdapter):
    provider_name = "statistics_feed_v1"

    def normalize(self, payload: dict[str, Any]) -> NormalizedStatisticsPayload:
        source = StatisticsFeedV1Payload.model_validate(payload)
        return NormalizedStatisticsPayload.model_validate(source.model_dump())

    def extract_fixture_reference(self, payload: dict[str, Any]) -> tuple[str | None, str | None]:
        fixture = payload.get("fixture")
        if not isinstance(fixture, dict):
            return None, None
        provider, identifier = fixture.get("provider"), fixture.get("id")
        return (
            str(provider) if provider is not None else None,
            str(identifier) if identifier is not None else None,
        )
