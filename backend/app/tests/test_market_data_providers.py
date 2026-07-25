"""Unit tests for source-provider isolation and odds normalization."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest

from app.modules.market_data.exceptions import (
    OddsPayloadValidationError,
    OddsProviderAlreadyRegisteredError,
    UnknownOddsProviderError,
)
from app.modules.market_data.providers.odds_feed_v1 import OddsFeedV1Adapter
from app.modules.market_data.providers.registry import OddsProviderRegistry, build_default_registry


def odds_feed_payload() -> dict[str, object]:
    """Return a valid reference provider payload used only by Market Data tests."""
    return {
        "fixture": {"provider": "fixture_feed_v1", "id": "fixture-100"},
        "bookmaker": {
            "id": "bookmaker-100",
            "name": "TITAN Sportsbook",
            "code": "titan",
        },
        "observed_at": "2026-08-01T12:00:00+00:00",
        "markets": [
            {
                "id": "market-1x2",
                "market_type": {"code": "match_winner", "name": "Match Winner"},
                "status": "OPEN",
                "period": "full_time",
                "selections": [
                    {"id": "selection-home", "key": "home", "name": "Home", "decimal_odds": "1.80"},
                    {"id": "selection-draw", "key": "draw", "name": "Draw", "decimal_odds": "3.50"},
                    {"id": "selection-away", "key": "away", "name": "Away", "decimal_odds": "4.20"},
                ],
            }
        ],
    }


def test_reference_adapter_normalizes_odds_into_provider_neutral_contract() -> None:
    """Provider status, market, selection, and decimal odds map into canonical DTOs."""
    normalized = OddsFeedV1Adapter().normalize(odds_feed_payload())

    assert normalized.fixture_provider_name == "fixture_feed_v1"
    assert normalized.bookmaker.code == "titan"
    assert normalized.markets[0].status_code == "open"
    assert normalized.markets[0].selections[0].implied_probability == Decimal("0.55555556")
    assert normalized.markets[0].line_key == "none"


def test_reference_adapter_rejects_unknown_market_status() -> None:
    """Unknown source market status cannot reach canonical market state resolution."""
    payload = odds_feed_payload()
    markets = payload["markets"]
    assert isinstance(markets, list)
    assert isinstance(markets[0], dict)
    markets[0]["status"] = "unpriced"

    with pytest.raises(OddsPayloadValidationError) as exc_info:
        OddsFeedV1Adapter().normalize(payload)

    assert exc_info.value.errors[0]["type"] == "unsupported_market_status"


def test_reference_adapter_rejects_duplicate_selection_identity() -> None:
    """One provider market cannot ambiguously describe the same source selection twice."""
    payload = deepcopy(odds_feed_payload())
    markets = payload["markets"]
    assert isinstance(markets, list)
    assert isinstance(markets[0], dict)
    selections = markets[0]["selections"]
    assert isinstance(selections, list)
    selections.append(deepcopy(selections[0]))

    with pytest.raises(OddsPayloadValidationError) as exc_info:
        OddsFeedV1Adapter().normalize(payload)

    assert exc_info.value.errors[0]["type"] == "value_error"


def test_odds_provider_registry_is_explicit_and_extensible() -> None:
    """Provider registration prevents duplicate business logic and unknown source execution."""
    registry = OddsProviderRegistry()
    adapter = OddsFeedV1Adapter()
    registry.register(adapter)

    assert registry.get(adapter.provider_name) is adapter
    with pytest.raises(OddsProviderAlreadyRegisteredError):
        registry.register(adapter)
    with pytest.raises(UnknownOddsProviderError):
        registry.get("unconfigured_odds_provider")
    assert build_default_registry().provider_names == ("odds_feed_v1",)
