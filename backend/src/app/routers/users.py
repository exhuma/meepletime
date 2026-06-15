"""User profile router: avatar upload, serving, and removal."""

from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.user_image import UserImage
from app.schemas.user import UserOut
from app.services.avatar import resolve_avatar_ref

router = APIRouter(prefix="/users", tags=["users"])


def _user_out(user: User, image: UserImage | None) -> UserOut:
    """
    Build a UserOut with the resolved avatar reference.

    :param user: The user being represented.
    :param image: The user's uploaded image row, if any.
    :returns: A UserOut including ``avatar_ref``.
    """
    out = UserOut.model_validate(user)
    out.avatar_ref = resolve_avatar_ref(user, image)
    return out


@router.post("/me/image", response_model=UserOut)
def upload_my_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> UserOut:
    """
    Upload (or replace) the authenticated user's profile picture.

    \r

    :raises HTTPException: 400 for an unsupported content type, 413
        when the payload exceeds ``CIRCLE_IMAGE_MAX_BYTES``.
    """
    content_type = file.content_type or ""
    if content_type not in settings.CIRCLE_IMAGE_ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type",
        )

    data = file.file.read()
    if len(data) > settings.CIRCLE_IMAGE_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image is too large",
        )

    image = db.execute(
        select(UserImage).where(UserImage.user_id == current_user.id)
    ).scalar_one_or_none()
    if image is None:
        image = UserImage(user_id=current_user.id)
        db.add(image)
    image.content_type = content_type
    image.data = data

    db.flush()
    db.refresh(image)
    db.commit()
    return _user_out(current_user, image)


@router.get("/{user_id}/image")
def get_user_image(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    """
    Return a user's profile-picture bytes.

    Public (no authentication): the unguessable user UUID acts as the
    access capability, mirroring the public circle-image endpoint.
    Responses are cacheable because the caller's URL is versioned via
    the ``v`` query param.

    \r

    :raises HTTPException: 404 when the user has no stored image.
    """
    image = db.execute(
        select(UserImage).where(UserImage.user_id == user_id)
    ).scalar_one_or_none()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image for this user",
        )
    return Response(
        content=image.data,
        media_type=image.content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.delete("/me/image", response_model=UserOut)
def delete_my_image(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """
    Remove the authenticated user's profile picture.

    Falls back through the avatar chain (IDP picture, then gravatar,
    then initials) once the uploaded image is gone.
    """
    image = db.execute(
        select(UserImage).where(UserImage.user_id == current_user.id)
    ).scalar_one_or_none()
    if image is not None:
        db.delete(image)
        db.commit()
    return _user_out(current_user, None)
