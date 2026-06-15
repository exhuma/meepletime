"""Avatar resolution: pick the best profile picture for a user.

The resolution order is, most-specific first:

1. A profile picture the user uploaded (served from ``user_images``).
2. The identity provider's ``picture`` claim, captured at
   provisioning.
3. A pluggable avatar provider, defaulting to the well-known Gravatar
   service. The Gravatar URL uses ``d=404`` so that the frontend can
   fall back to its initials avatar when no Gravatar exists.

The frontend treats the resolved reference as a plain image source and
shows the initials avatar whenever the image fails to load, which is
what closes the chain at step 4 (initials).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Protocol

from app.models.user import User
from app.models.user_image import UserImage


class AvatarProvider(Protocol):
    """A source of fallback avatar URLs derived from an email."""

    def url_for(self, email: str) -> str | None:
        """
        Return an avatar URL for the given email, or ``None``.

        :param email: The account email to derive an avatar from.
        :returns: An absolute URL, or ``None`` when unsupported.
        """
        ...


class GravatarProvider:
    """
    Avatar provider backed by the well-known Gravatar service.

    Uses ``d=404`` so a missing Gravatar yields an HTTP 404 rather than
    a generated placeholder, letting the client fall back to initials.
    """

    BASE_URL = "https://www.gravatar.com/avatar/"

    def url_for(self, email: str) -> str | None:
        """
        Build the Gravatar URL for ``email``.

        :param email: The account email to derive the hash from.
        :returns: A Gravatar URL, or ``None`` when email is empty.
        """
        normalized = email.strip().lower()
        if not normalized:
            return None
        digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
        return f"{self.BASE_URL}{digest}?d=404&s=256"


# The default provider; decoupled so an alternative can be injected.
DEFAULT_AVATAR_PROVIDER: AvatarProvider = GravatarProvider()


def _uploaded_image_ref(user_id: uuid.UUID, image: UserImage) -> str:
    """
    Build the API-relative URL for an uploaded profile picture.

    :param user_id: Owning user identifier.
    :param image: Persisted image row (``updated_at`` must be set).
    :returns: Path such as ``/users/<id>/image?v=<epoch>``.
    """
    version = int(image.updated_at.timestamp())
    return f"/users/{user_id}/image?v={version}"


def resolve_avatar_ref(
    user: User,
    image: UserImage | None,
    provider: AvatarProvider = DEFAULT_AVATAR_PROVIDER,
) -> str | None:
    """
    Resolve the best avatar reference for ``user``.

    :param user: The user whose avatar is being resolved.
    :param image: The user's uploaded image row, if any.
    :param provider: Fallback avatar provider (default Gravatar).
    :returns: An image reference (API-relative path or absolute URL),
        or ``None`` when nothing resolves and the client should render
        its initials avatar.
    """
    if image is not None:
        return _uploaded_image_ref(user.id, image)
    if user.picture_url:
        return user.picture_url
    return provider.url_for(user.email)
