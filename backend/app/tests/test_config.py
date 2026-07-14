"""Environment configuration tests."""

from pytest import MonkeyPatch

from app.core.config import AppEnvironment, Settings


def test_settings_load_from_environment(monkeypatch: MonkeyPatch) -> None:
    """Settings parse prefixed environment values and comma-separated origins."""
    monkeypatch.setenv("TITAN_APP_ENV", "testing")
    monkeypatch.setenv("TITAN_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
    monkeypatch.setenv("TITAN_REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("TITAN_CORS_ORIGINS", "http://localhost:5000,http://localhost:3000")

    settings = Settings(_env_file=None)

    assert settings.app_env is AppEnvironment.TESTING
    assert settings.database_url.endswith("/test")
    assert settings.cors_origins == ["http://localhost:5000", "http://localhost:3000"]
