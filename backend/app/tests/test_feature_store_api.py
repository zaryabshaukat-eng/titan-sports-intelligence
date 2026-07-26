"""OpenAPI registration coverage for Feature Store generation and retrieval contracts."""

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_feature_store_endpoints_are_versioned_and_protected() -> None:
    app = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))
    paths = app.openapi()["paths"]

    assert "/api/v1/feature-store/generations" in paths
    assert "/api/v1/feature-store/feature-sets" in paths
    assert (
        "/api/v1/feature-store/feature-sets/{feature_set_code}/versions/"
        "{feature_set_version}/definitions"
    ) in paths
    assert "/api/v1/feature-store/features" in paths
    assert "/api/v1/feature-store/features/{feature_value_id}/lineage" in paths
    assert paths["/api/v1/feature-store/generations"]["post"]["security"] == [{"HTTPBearer": []}]
    assert set(paths["/api/v1/feature-store/features"]) == {"get"}
