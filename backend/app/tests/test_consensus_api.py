"""OpenAPI coverage for Consensus Engine endpoints."""

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_consensus_api_is_versioned_and_protected() -> None:
    paths = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING)).openapi()["paths"]
    assert "/api/v1/consensus/strategies" in paths
    assert "/api/v1/consensus/runs" in paths
    assert "/api/v1/consensus/runs/{run_id}/outputs" in paths
    assert "/api/v1/consensus/runs/{run_id}/confidence-metrics" in paths
    assert paths["/api/v1/consensus/runs"]["post"]["security"] == [{"HTTPBearer": []}]
