"""Ensure every existing outbox table exposes the shared delivery-control fields."""

from app.modules.ingestion.models import IngestionOutboxEvent
from app.modules.market_data.models import MarketDataOutboxEvent
from app.modules.statistics.models import StatisticsOutboxEvent


def test_all_outbox_models_have_delivery_metadata() -> None:
    required = {
        "delivery_attempts",
        "next_attempt_at",
        "lease_owner",
        "lease_expires_at",
        "last_error",
        "dead_lettered_at",
    }
    for model in (IngestionOutboxEvent, MarketDataOutboxEvent, StatisticsOutboxEvent):
        assert required <= set(model.__table__.c.keys())
