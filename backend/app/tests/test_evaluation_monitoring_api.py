from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_monitoring_openapi_and_authorization_are_registered() -> None:
    paths = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING)).openapi()["paths"]
    assert "/api/v1/evaluation-monitoring/run" in paths
    assert paths["/api/v1/evaluation-monitoring/run"]["post"]["security"] == [{"HTTPBearer": []}]
