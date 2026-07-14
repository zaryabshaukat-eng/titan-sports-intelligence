"""Environment-backed, validated application settings."""

from __future__ import annotations

import json
from enum import StrEnum
from functools import lru_cache
from typing import Any

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


_DEVELOPMENT_SECRET = "local-development-secret-change-before-production"


class Settings(BaseSettings):
    """Validated runtime settings sourced from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TITAN_",
        case_sensitive=False,
        enable_decoding=False,
        extra="ignore",
    )

    app_name: str = "TITAN Core"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    docs_enabled: bool = True
    metrics_enabled: bool = True

    database_url: str = "postgresql+asyncpg://titan:titan@localhost:5432/titan"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = ["http://localhost:5000"]
    cors_allow_credentials: bool = True
    trusted_hosts: list[str] = []

    secret_key: SecretStr = SecretStr(_DEVELOPMENT_SECRET)

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def parse_list_setting(cls, value: Any) -> Any:
        """Accept JSON arrays and convenient comma-separated environment values."""
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            return []
        if normalized.startswith("["):
            return json.loads(normalized)
        return [item.strip() for item in normalized.split(",") if item.strip()]

    @field_validator("database_url")
    @classmethod
    def require_async_postgresql_url(cls, value: str) -> str:
        """Ensure the application uses the supported asynchronous PostgreSQL driver."""
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must use the postgresql+asyncpg:// scheme")
        return value

    @field_validator("redis_url")
    @classmethod
    def require_redis_url(cls, value: str) -> str:
        """Reject accidental non-Redis connection strings at startup."""
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("redis_url must use redis:// or rediss://")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        """Fail fast when an unsafe development configuration reaches production."""
        if self.app_env is not AppEnvironment.PRODUCTION:
            return self

        if self.secret_key.get_secret_value() == _DEVELOPMENT_SECRET:
            raise ValueError("TITAN_SECRET_KEY must be changed in production")
        if self.docs_enabled:
            raise ValueError("interactive API documentation must be disabled in production")
        if not self.cors_origins or "*" in self.cors_origins:
            raise ValueError("production requires explicit CORS origins")
        if any("localhost" in origin for origin in self.cors_origins):
            raise ValueError("localhost is not a permitted production CORS origin")
        return self

    @property
    def is_production(self) -> bool:
        """Return whether this process is serving a production environment."""
        return self.app_env is AppEnvironment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for the lifetime of the process."""
    return Settings()
