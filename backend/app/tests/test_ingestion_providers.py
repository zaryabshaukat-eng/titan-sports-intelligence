"""Unit tests for provider isolation and fixture normalization."""

from __future__ import annotations

from copy import deepcopy

import pytest

from app.modules.ingestion.exceptions import (
    PayloadValidationError,
    ProviderAlreadyRegisteredError,
    UnknownProviderError,
)
from app.modules.ingestion.providers.fixture_feed_v1 import FixtureFeedV1Adapter
from app.modules.ingestion.providers.registry import FixtureProviderRegistry, build_default_registry


def fixture_feed_payload() -> dict[str, object]:
    """Return a complete fixture_feed_v1 payload used only by ingestion tests."""
    return {
        "fixture": {
            "id": "fixture-100",
            "kickoff": "2026-08-01T15:00:00+00:00",
            "scheduled_end": "2026-08-01T17:00:00+00:00",
            "status": "SCHEDULED",
            "timezone": "Europe/London",
            "round": "Round 1",
            "stage": "Regular Season",
            "venue": {
                "id": "venue-100",
                "name": "TITAN Stadium",
                "city": "London",
                "country_iso_code": "GB",
                "timezone": "Europe/London",
            },
        },
        "sport": "football",
        "country": {
            "id": "country-gb",
            "name": "United Kingdom",
            "iso_code": "gb",
            "iso3_code": "gbr",
        },
        "league": {"id": "league-100", "name": "English Football League"},
        "competition": {"id": "competition-100", "name": "Premier League", "type": "league"},
        "season": {
            "id": "season-2026",
            "name": "2026/27",
            "start_date": "2026-08-01",
            "end_date": "2027-05-31",
            "status": "planned",
        },
        "teams": {
            "home": {
                "id": "team-home",
                "name": "Home FC",
                "type": "club",
                "country_iso_code": "GB",
            },
            "away": {
                "id": "team-away",
                "name": "Away FC",
                "type": "club",
                "country_iso_code": "GB",
            },
        },
        "officials": [
            {
                "id": "official-1",
                "name": "Referee Example",
                "role": "referee",
                "country_iso_code": "GB",
            }
        ],
    }


def test_reference_adapter_normalizes_provider_vocabulary() -> None:
    """Provider fields are translated into a provider-neutral canonical DTO."""
    normalized = FixtureFeedV1Adapter().normalize(fixture_feed_payload())

    assert normalized.provider_fixture_id == "fixture-100"
    assert normalized.fixture_status_code == "scheduled"
    assert normalized.country.iso_code == "GB"
    assert normalized.competition.competition_type.value == "league"
    assert normalized.timezone_iana_name == "Europe/London"
    assert normalized.officials[0].role.value == "referee"


def test_reference_adapter_rejects_missing_required_provider_structure() -> None:
    """Invalid provider JSON produces audit-safe structured validation errors."""
    payload = deepcopy(fixture_feed_payload())
    del payload["fixture"]

    with pytest.raises(PayloadValidationError) as exc_info:
        FixtureFeedV1Adapter().normalize(payload)

    assert exc_info.value.errors[0]["path"] == "fixture"


def test_reference_adapter_rejects_unknown_status() -> None:
    """Unsupported provider statuses cannot leak into canonical fixture state."""
    payload = fixture_feed_payload()
    fixture = payload["fixture"]
    assert isinstance(fixture, dict)
    fixture["status"] = "weather_hold"

    with pytest.raises(PayloadValidationError) as exc_info:
        FixtureFeedV1Adapter().normalize(payload)

    assert exc_info.value.errors[0]["type"] == "unsupported_status"


def test_provider_registry_is_explicit_and_prevents_duplicate_business_logic() -> None:
    """A provider is registered once and unknown provider names fail safely."""
    registry = FixtureProviderRegistry()
    adapter = FixtureFeedV1Adapter()
    registry.register(adapter)

    assert registry.get(adapter.provider_name) is adapter
    with pytest.raises(ProviderAlreadyRegisteredError):
        registry.register(adapter)
    with pytest.raises(UnknownProviderError):
        registry.get("unconfigured_provider")
    assert build_default_registry().provider_names == ("fixture_feed_v1",)
