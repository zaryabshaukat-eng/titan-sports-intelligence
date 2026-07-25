"""Authorization boundary tests for configured development principals."""

from fastapi.testclient import TestClient

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_protected_ingestion_requires_a_bearer_credential() -> None:
    with TestClient(create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))) as client:
        response = client.post("/api/v1/ingestion/fixtures/fixture_feed_v1", json={"payloads": []})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_analyst_cannot_invoke_fixture_ingestion() -> None:
    settings = Settings(
        _env_file=None,
        app_env=AppEnvironment.TESTING,
        development_identity_credentials={
            "analyst-token": {"subject": "analyst", "roles": ["analyst"]}
        },
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/ingestion/fixtures/fixture_feed_v1",
            headers={"Authorization": "Bearer analyst-token"},
            json={"payloads": [{"untrusted": "payload"}]},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "authorization_denied"
