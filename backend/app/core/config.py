"""Application configuration.

All runtime configuration is sourced from environment variables and validated
at startup via Pydantic. This means the application fails fast with a clear
error if misconfigured, rather than failing unpredictably at request time.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings, loaded from environment/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata ---
    app_name: str = "Task Manager API"
    environment: Literal["development", "testing", "production"] = "development"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: PostgresDsn

    # --- Security / JWT ---
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Redis (optional cache layer; app degrades gracefully if unset/unreachable) ---
    redis_url: str | None = None
    cache_ttl_seconds: int = 30

    # --- Pagination ---
    default_page_size: int = 10
    max_page_size: int = 100

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_not_be_placeholder(cls, v: str) -> str:
        """Refuse obviously-unsafe default secrets so misconfiguration is loud."""
        if v.lower() in {"changeme", "secret", "your-secret-key"}:
            raise ValueError(
                "secret_key must be replaced with a real random value, "
                "e.g. `openssl rand -hex 32`"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor.

    lru_cache ensures the environment is parsed/validated exactly once per
    process rather than on every request, and gives us a single override
    point (`get_settings.cache_clear()`) for tests.
    """
    return Settings()
