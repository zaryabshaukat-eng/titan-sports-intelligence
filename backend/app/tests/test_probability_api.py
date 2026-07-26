"""OpenAPI registration coverage for protected Probability Engine contracts."""

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_probability_endpoints_are_versioned_and_protected() -> None:
    """Probability execution and evidence retrieval are exposed only through versioned APIs."""
    app = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))
    paths = app.openapi()["paths"]

    assert "/api/v1/probability/models" in paths
    assert "/api/v1/probability/calibrations" in paths
    assert "/api/v1/probability/runs" in paths
    assert "/api/v1/probability/runs/{probability_run_id}/outputs" in paths
    assert "/api/v1/probability/runs/{probability_run_id}/evaluations" in paths
    assert "/api/v1/probability/runs/{probability_run_id}/lineage" in paths
    assert paths["/api/v1/probability/runs"]["post"]["security"] == [{"HTTPBearer": []}]
    assert paths["/api/v1/probability/models"]["get"]["security"] == [{"HTTPBearer": []}]
