#!/usr/bin/env python
"""
Mint a self-signed HS256 JWT for headless API testing.

This script is for **development and headless coding-agent
environments only**.  It MUST NOT be used in production.

The generated token is accepted by the FastAPI backend only
when ``DEV_SHARED_SECRET`` is set in ``backend/.env``.  That
variable must never be configured in production deployments.

Usage (from the repository root)::

    task dev:token
    task dev:token -- --sub myagent --email agent@dev.local
    task dev:token -- --ttl 3600
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta

import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict


class _DevSettings(BaseSettings):
    DEV_SHARED_SECRET: str
    OIDC_ISSUER: str
    OIDC_AUDIENCE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def main() -> None:
    """Parse CLI arguments, mint a JWT, and print it to stdout."""
    parser = argparse.ArgumentParser(
        description="Mint a dev JWT for headless API testing",
    )
    parser.add_argument(
        "--sub",
        default="dev-agent",
        help="Subject claim (default: dev-agent)",
    )
    parser.add_argument(
        "--email",
        default="dev-agent@meepletime.local",
        help="Email claim",
    )
    parser.add_argument(
        "--name",
        default="Dev Agent",
        help="Display name claim",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=365 * 24 * 3600,
        help=("Token lifetime in seconds (default: %(default)s — one year)"),
    )
    args = parser.parse_args()

    try:
        settings = _DevSettings()
    except Exception as exc:  # pydantic ValidationError or similar
        print(f"Error loading settings: {exc}", file=sys.stderr)
        print(
            "Ensure DEV_SHARED_SECRET is set in backend/.env",
            file=sys.stderr,
        )
        sys.exit(1)

    now = datetime.now(tz=UTC)
    payload = {
        "iss": settings.OIDC_ISSUER,
        "aud": settings.OIDC_AUDIENCE,
        "sub": args.sub,
        "email": args.email,
        "name": args.name,
        "iat": now,
        "exp": now + timedelta(seconds=args.ttl),
    }
    token: str = jwt.encode(
        payload,
        settings.DEV_SHARED_SECRET,
        algorithm="HS256",
    )
    print(token)


if __name__ == "__main__":
    main()
