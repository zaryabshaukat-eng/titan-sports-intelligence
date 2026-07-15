"""Provider adapter implementations and application registry composition."""

from app.modules.ingestion.providers.fixture_feed_v1 import FixtureFeedV1Adapter
from app.modules.ingestion.providers.registry import FixtureProviderRegistry, build_default_registry

__all__ = ["FixtureFeedV1Adapter", "FixtureProviderRegistry", "build_default_registry"]
