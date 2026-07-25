"""OpenAPI coverage for protected Market Data ingestion and read-only endpoints."""

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_market_data_endpoints_are_documented_and_protected() -> None:
    """Internal contracts expose versioned bearer-authenticated OpenAPI operations."""
    app = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))
    paths = app.openapi()["paths"]

    assert "/api/v1/market-data/ingestion/odds/{provider_name}" in paths
    assert "/api/v1/market-data/bookmakers" in paths
    assert "/api/v1/market-data/markets" in paths
    assert "/api/v1/market-data/odds-history" in paths
    assert "/api/v1/market-data/latest-odds" in paths
    assert "/api/v1/market-data/movement-history" in paths
    assert paths["/api/v1/market-data/ingestion/odds/{provider_name}"]["post"]["security"] == [
        {"HTTPBearer": []}
    ]
    assert set(paths["/api/v1/market-data/odds-history"]) == {"get"}
