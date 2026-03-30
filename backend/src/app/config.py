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
    :param DEV_SHARED_SECRET: When set, the backend accepts
        self-minted HS256 JWTs (signed with this secret) instead
        of validating tokens via Keycloak JWKS.  **Development
        and headless-agent use only. Never set in production.**
    :param NOTIFICATION_DEBOUNCE_SECONDS: Debounce window for
        notification coalescing, in seconds.
    :param FRONTEND_URL: Allowed CORS origin for the Vue frontend.
    :param CORS_ORIGINS: Allowed CORS origins for API requests.
    :param INVITE_REGEN_LIMIT: Max invite regeneration requests
        allowed per window for a user+IP key.
    :param INVITE_REGEN_WINDOW_SECONDS: Sliding-window size in
        seconds for invite regeneration throttling.
    """

    DATABASE_URL: PostgresDsn
    OIDC_AUTHORITY: str
    OIDC_AUDIENCE: str
    OIDC_ISSUER: str
    DEV_SHARED_SECRET: str | None = None
    NOTIFICATION_DEBOUNCE_SECONDS: int = 10
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    INVITE_REGEN_LIMIT: int = 5
    INVITE_REGEN_WINDOW_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="MEEPLETIME_",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    :returns: Singleton Settings loaded from the environment.
    """
    return Settings()
