"""Pure unit tests for deterministic immutable-payload and market-line helpers."""

from decimal import Decimal

from app.modules.market_data.schemas import market_line_key
from app.modules.market_data.service import idempotency_key, payload_checksum


def test_odds_payload_checksum_is_stable_for_equivalent_json_key_order() -> None:
    """Retry safety is based on canonical JSON content rather than object key ordering."""
    first = {"fixture": {"id": "fixture-100"}, "observed_at": "2026-08-01T12:00:00+00:00"}
    second = {"observed_at": "2026-08-01T12:00:00+00:00", "fixture": {"id": "fixture-100"}}

    checksum = payload_checksum(first)
    assert checksum == payload_checksum(second)
    assert idempotency_key("odds_feed_v1", checksum) == idempotency_key("odds_feed_v1", checksum)
    assert idempotency_key("other_provider", checksum) != idempotency_key("odds_feed_v1", checksum)


def test_market_line_key_distinguishes_missing_and_decimal_market_lines() -> None:
    """Market natural keys remain stable across numeric formatting variations."""
    assert market_line_key(None) == "none"
    assert market_line_key(Decimal("2.50")) == "2.5"
    assert market_line_key(Decimal("0.000")) == "0"
