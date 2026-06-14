"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from the environment.

    :param DATABASE_URL: PostgreSQL connection string.
    :param OIDC_AUTHORITY: OIDC discovery base URL (Keycloak realm
        URL) the backend fetches metadata/JWKS from.
    :param OIDC_AUDIENCE: Expected audience claim in access tokens.
    :param OIDC_ISSUER: Expected ``iss`` claim in access tokens.
        Optional; defaults to ``OIDC_AUTHORITY`` when unset, since
        for most providers (Keycloak included) the issuer equals the
        discovery URL. Override only when the backend reaches the IDP
        over a different host than the public issuer in tokens.
    :param DEV_SHARED_SECRET: When set, the backend accepts
        self-minted HS256 JWTs (signed with this secret) instead
        of validating tokens via Keycloak JWKS.  **Development
        and headless-agent use only. Never set in production.**
    :param DEV_AUTH_ENABLED: When true, mounts the ``/auth/dev/*``
        in-app dev-login endpoints so the SPA can authenticate
        without Keycloak. Requires ``DEV_SHARED_SECRET`` (used to
        sign the minted tokens). **Development and headless-agent
        use only. Never enable in production.**
    :param NOTIFICATION_DEBOUNCE_SECONDS: Debounce window for
        notification coalescing, in seconds.
    :param EMAIL_CONFIRMATION_TTL_HOURS: Validity window, in hours,
        for a notification-email confirmation link.
    :param FRONTEND_URL: Allowed CORS origin for the Vue frontend.
    :param CORS_ORIGINS: Allowed CORS origins for API requests.
    :param INVITE_REGEN_LIMIT: Max invite regeneration requests
        allowed per window for a user+IP key.
    :param INVITE_REGEN_WINDOW_SECONDS: Sliding-window size in
        seconds for invite regeneration throttling.
    :param APP_BASE_URL: Public base URL of the frontend, used to
        build deep links inside notification bodies.
    :param SMTP_HOST: SMTP server host. Email delivery is inert
        when unset.
    :param SMTP_PORT: SMTP server port (STARTTLS submission).
    :param SMTP_USERNAME: SMTP auth username, if required.
    :param SMTP_PASSWORD: SMTP auth password, if required.
    :param SMTP_FROM: ``From`` address for notification emails.
    :param SMTP_USE_TLS: Use STARTTLS when connecting.
    :param VAPID_PUBLIC_KEY: VAPID public key (base64url) exposed to
        browsers for Web Push subscription.
    :param VAPID_PRIVATE_KEY: VAPID private key (server-only, never
        exposed). Web Push is inert when unset.
    :param VAPID_SUBJECT: VAPID ``sub`` claim, e.g.
        ``mailto:ops@example.com``.
    :param CIRCLE_IMAGE_MAX_BYTES: Maximum accepted size, in bytes,
        for an uploaded circle hero image.
    :param CIRCLE_IMAGE_ALLOWED_TYPES: Accepted ``Content-Type``
        values for uploaded circle hero images.
    """

    DATABASE_URL: PostgresDsn
    OIDC_AUTHORITY: str
    OIDC_AUDIENCE: str
    OIDC_ISSUER: str | None = None
    DEV_SHARED_SECRET: str | None = None
    DEV_AUTH_ENABLED: bool = False
    NOTIFICATION_DEBOUNCE_SECONDS: int = 10
    EMAIL_CONFIRMATION_TTL_HOURS: int = 24
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    INVITE_REGEN_LIMIT: int = 5
    INVITE_REGEN_WINDOW_SECONDS: int = 60
    APP_BASE_URL: str = "http://localhost:5173"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_USE_TLS: bool = True
    VAPID_PUBLIC_KEY: str | None = None
    VAPID_PRIVATE_KEY: str | None = None
    VAPID_SUBJECT: str | None = None
    CIRCLE_IMAGE_MAX_BYTES: int = 5 * 1024 * 1024
    CIRCLE_IMAGE_ALLOWED_TYPES: set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="MEEPLETIME_",
    )

    @model_validator(mode="after")
    def _default_issuer_to_authority(self) -> Settings:
        """
        Default the expected issuer to the authority URL.

        For Keycloak (Option A) and most OIDC providers the token
        ``iss`` claim equals the discovery (authority) URL, so
        operators normally set only ``OIDC_AUTHORITY``.

        :returns: The settings instance with ``OIDC_ISSUER`` resolved.
        """
        if self.OIDC_ISSUER is None:
            self.OIDC_ISSUER = self.OIDC_AUTHORITY
        return self

    @model_validator(mode="after")
    def _require_secret_for_dev_auth(self) -> Settings:
        """
        Ensure the dev-login endpoints have a secret to sign with.

        ``DEV_AUTH_ENABLED`` mints HS256 tokens that the same
        ``DEV_SHARED_SECRET`` then verifies, so the signer must
        equal the verifier. Fail loudly on misconfiguration rather
        than silently generating an ephemeral secret.

        :returns: The validated settings instance.
        :raises ValueError: When dev auth is enabled without a
            shared secret.
        """
        if self.DEV_AUTH_ENABLED and self.DEV_SHARED_SECRET is None:
            raise ValueError(
                "MEEPLETIME_DEV_AUTH_ENABLED requires "
                "MEEPLETIME_DEV_SHARED_SECRET to be set"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    :returns: Singleton Settings loaded from the environment.
    """
    return Settings()
