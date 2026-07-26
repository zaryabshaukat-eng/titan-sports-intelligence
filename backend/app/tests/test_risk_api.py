from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_risk_api_remains_versioned_and_protected() -> None:
    paths = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING)).openapi()["paths"]
    assert "/api/v1/risk/runs" in paths
    assert paths["/api/v1/risk/runs"]["post"]["security"] == [{"HTTPBearer": []}]
