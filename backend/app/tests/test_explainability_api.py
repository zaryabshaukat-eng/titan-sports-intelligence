from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_explainability_api_is_versioned_and_protected() -> None:
    paths = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING)).openapi()["paths"]
    assert "/api/v1/explainability/runs" in paths
    assert "/api/v1/explainability/explanations/{id}/evidence" in paths
    assert paths["/api/v1/explainability/runs"]["post"]["security"] == [{"HTTPBearer": []}]
