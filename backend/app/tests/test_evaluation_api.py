from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_evaluation_api_is_versioned_and_protected() -> None:
    paths = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING)).openapi()["paths"]
    assert "/api/v1/evaluation/backtests" in paths and "/api/v1/evaluation/scenarios" in paths
    assert "/api/v1/evaluation/backtests/{id}" in paths
    assert "/api/v1/evaluation/comparisons" in paths
    assert paths["/api/v1/evaluation/backtests"]["post"]["security"] == [{"HTTPBearer": []}]
