"""Unit tests for public Sports API registration and OpenAPI visibility."""

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_sports_read_endpoints_are_included_in_openapi() -> None:
    """Canonical Sports resources are available only through versioned API paths."""
    app = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))
    paths = app.openapi()["paths"]

    assert "/api/v1/sports/countries" in paths
    assert "/api/v1/sports/fixtures" in paths
    assert "/api/v1/sports/fixture-statuses" in paths
    assert set(paths["/api/v1/sports/countries"]) == {"get"}
    assert set(paths["/api/v1/sports/fixtures"]) == {"get"}
