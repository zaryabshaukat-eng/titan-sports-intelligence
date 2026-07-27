"""Environment configuration tests."""

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from app.core.config import AppEnvironment, Settings


def test_settings_load_from_environment(monkeypatch: MonkeyPatch) -> None:
    """Settings parse prefixed environment values and comma-separated origins."""
    monkeypatch.setenv("TITAN_APP_ENV", "testing")
    monkeypatch.setenv("TITAN_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
    monkeypatch.setenv("TITAN_REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("TITAN_CORS_ORIGINS", "http://localhost:5000,http://localhost:3000")
    monkeypatch.setenv("TITAN_OUTBOX_RETRY_BACKOFF_MULTIPLIER", "3")
    monkeypatch.setenv("TITAN_OUTBOX_SHUTDOWN_TIMEOUT_SECONDS", "12.5")

    settings = Settings(_env_file=None)

    assert settings.app_env is AppEnvironment.TESTING
    assert settings.database_url.endswith("/test")
    assert settings.cors_origins == ["http://localhost:5000", "http://localhost:3000"]
    assert settings.outbox_retry_backoff_multiplier == 3
    assert settings.outbox_shutdown_timeout_seconds == 12.5


def _production_settings(**overrides: object) -> Settings:
    """Return the minimum explicit configuration permitted for a production process."""
    values: dict[str, object] = {
        "_env_file": None,
        "app_env": AppEnvironment.PRODUCTION,
        "secret_key": "production-secret-not-the-development-default",
        "docs_enabled": False,
        "cors_origins": ["https://console.titan.example"],
        "identity_provider": "jwt",
        "jwt_issuer": "https://identity.titan.example",
        "jwt_audience": "titan-core",
        "jwt_hs256_secret": "production-jwt-secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_settings_fail_closed_for_development_controls() -> None:
    """Production startup rejects the default secret, docs, localhost CORS, and dev identity."""
    for overrides in (
        {"secret_key": "local-development-secret-change-before-production"},
        {"docs_enabled": True},
        {"cors_origins": ["http://localhost:5000"]},
        {"identity_provider": "development"},
        {"jwt_hs256_secret": None},
    ):
        with pytest.raises(ValidationError):
            _production_settings(**overrides)


def test_production_settings_accept_explicit_jwt_configuration() -> None:
    """A minimally secure deployment configuration remains valid and deterministic."""
    settings = _production_settings()

    assert settings.is_production is True
    assert settings.docs_enabled is False
    assert settings.identity_provider == "jwt"
