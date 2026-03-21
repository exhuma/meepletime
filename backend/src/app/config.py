"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from the environment.

    :param DATABASE_URL: PostgreSQL connection string.
    :param OIDC_AUTHORITY: OIDC issuer base URL (Keycloak realm URL).
    :param OIDC_AUDIENCE: Expected audience claim in access tokens.
    :param OIDC_ISSUER: Expected iss claim in access tokens.
    :param NOTIFICATION_DEBOUNCE_SECONDS: Debounce window for
        notification coalescing, in seconds.
    :param FRONTEND_URL: Allowed CORS origin for the Vue frontend.
    """

    DATABASE_URL: PostgresDsn
    OIDC_AUTHORITY: str
    OIDC_AUDIENCE: str
    OIDC_ISSUER: str
    NOTIFICATION_DEBOUNCE_SECONDS: int = 10
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    :returns: Singleton Settings loaded from the environment.
    """
    return Settings()
