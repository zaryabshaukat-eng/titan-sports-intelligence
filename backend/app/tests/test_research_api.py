"""OpenAPI registration coverage for the protected Research Engine contracts."""

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_research_endpoints_are_versioned_and_protected() -> None:
    """Research writes require execution permission; immutable artifacts remain readable."""
    app = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))
    paths = app.openapi()["paths"]

    assert "/api/v1/research/datasets" in paths
    assert "/api/v1/research/datasets/{dataset_snapshot_id}/rows" in paths
    assert "/api/v1/research/experiments" in paths
    assert "/api/v1/research/experiments/{experiment_id}/statistics" in paths
    assert "/api/v1/research/experiments/{experiment_id}/lineage" in paths
    assert "/api/v1/research/hypotheses" in paths
    assert "/api/v1/research/hypotheses/evaluations" in paths
    assert paths["/api/v1/research/datasets"]["post"]["security"] == [{"HTTPBearer": []}]
    assert paths["/api/v1/research/experiments"]["get"]["security"] == [{"HTTPBearer": []}]
