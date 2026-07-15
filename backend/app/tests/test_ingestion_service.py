"""Pure unit tests for idempotency key and payload checksum behavior."""

from app.modules.ingestion.service import idempotency_key, payload_checksum


def test_checksum_is_stable_for_equivalent_json_object_key_order() -> None:
    """Retry safety is based on canonical JSON, not client object key ordering."""
    first = {"fixture": {"id": "fixture-100", "status": "scheduled"}, "sport": "football"}
    second = {"sport": "football", "fixture": {"status": "scheduled", "id": "fixture-100"}}

    first_checksum = payload_checksum(first)
    assert first_checksum == payload_checksum(second)
    assert idempotency_key("fixture_feed_v1", first_checksum) == idempotency_key(
        "fixture_feed_v1", first_checksum
    )
    assert idempotency_key("another_provider", first_checksum) != idempotency_key(
        "fixture_feed_v1", first_checksum
    )
