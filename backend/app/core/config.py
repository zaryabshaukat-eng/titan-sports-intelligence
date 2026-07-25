"""Environment-backed, validated application settings."""

from __future__ import annotations

import json
from enum import StrEnum
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


_DEVELOPMENT_SECRET = "local-development-secret-change-before-production"


class DevelopmentIdentityCredential(BaseModel):
    """One development-only bearer credential and its normalized identity claims."""

    subject: str
    organization_id: str | None = "development"
    roles: list[str]


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

    outbox_poll_interval_seconds: float = 1.0
    outbox_lease_seconds: int = 30
    outbox_batch_size: int = 100
    outbox_max_attempts: int = 8
    outbox_retry_initial_seconds: float = 1.0
    outbox_retry_max_seconds: float = 300.0
    outbox_retry_backoff_multiplier: float = 2.0
    outbox_shutdown_timeout_seconds: float = 30.0
    outbox_backlog_warning_threshold: int = 1_000
    slow_request_threshold_seconds: float = 1.0
    slow_query_threshold_seconds: float = 0.5
    outbox_retry_warning_threshold: int = 5
    worker_timeout_seconds: float = 30.0
    readiness_timeout_seconds: float = 2.0

    identity_provider: str = "development"
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    jwt_hs256_secret: SecretStr | None = None
    jwt_public_key_pem: SecretStr | None = None
    jwt_clock_skew_seconds: int = 30
    development_identity_credentials: dict[str, DevelopmentIdentityCredential] = {
        "titan-development-admin": DevelopmentIdentityCredential(
            subject="development-admin", roles=["titan_admin"]
        )
    }

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

    @field_validator("development_identity_credentials", mode="before")
    @classmethod
    def parse_development_credentials(cls, value: Any) -> Any:
        """Accept JSON credentials from environment without placing them in source control."""
        if isinstance(value, str):
            return json.loads(value)
        return value

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
        if self.identity_provider == "development":
            raise ValueError("production cannot use the development identity provider")
        if self.identity_provider == "jwt" and self.jwt_hs256_secret is None:
            raise ValueError("the jwt provider requires TITAN_JWT_HS256_SECRET in production")
        return self

    @property
    def is_production(self) -> bool:
        """Return whether this process is serving a production environment."""
        return self.app_env is AppEnvironment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for the lifetime of the process."""
    return Settings()
