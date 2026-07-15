"""OpenAPI registration tests for the protected fixture-ingestion boundary."""

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_fixture_ingestion_endpoint_is_documented_and_protected() -> None:
    """The internal import contract appears in OpenAPI with bearer authentication."""
    app = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))
    operation = app.openapi()["paths"]["/api/v1/ingestion/fixtures/{provider_name}"]["post"]

    assert operation["summary"] == "Ingest a provider fixture batch"
    assert operation["responses"]["202"]["description"] == "Successful Response"
    assert operation["security"] == [{"HTTPBearer": []}]
