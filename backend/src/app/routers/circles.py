"""Circles router: circle creation and management."""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import (
    get_circle_or_404,
    get_current_active_user,
    get_db,
    get_membership_or_403,
    require_admin_or_owner,
    require_owner,
)
from app.models.circle import Circle
from app.models.circle_image import CircleImage
from app.models.membership import CircleMembership, MemberRole
from app.models.user import User
from app.rate_limit import enforce_limit_or_429
from app.schemas.circle import CircleCreate, CircleOut, CircleUpdate
from app.schemas.membership import InviteJoin, MembershipOut
from app.services.invite import generate_unique_pin, normalize_pin
from app.utils import apply_partial_update

router = APIRouter(tags=["circles"])


def limit_invite_regeneration(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> None:
    """Throttle invite regeneration attempts by user and client IP."""
    client_host = request.client.host if request.client else "unknown"
    key = f"invite:{current_user.id}:{client_host}"
    enforce_limit_or_429(
        key=key,
        limit=settings.INVITE_REGEN_LIMIT,
        window_seconds=settings.INVITE_REGEN_WINDOW_SECONDS,
        scope="invite-regeneration",
    )


@router.get("/circles", response_model=list[CircleOut])
def list_circles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Circle]:
    """Return all circles that the authenticated user belongs to."""
    return list(
        db.execute(
            select(Circle)
            .join(
                CircleMembership,
                Circle.id == CircleMembership.circle_id,
            )
            .where(CircleMembership.user_id == current_user.id)
        )
        .scalars()
        .all()
    )


@router.post(
    "/circles", response_model=CircleOut, status_code=status.HTTP_201_CREATED
)
def create_circle(
    circle_in: CircleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """Create a new circle and automatically join the creator as owner."""
    for attempt in range(2):
        circle = Circle(
            **circle_in.model_dump(),
            created_by_user_id=current_user.id,
            invite_token=generate_unique_pin(db),
        )
        db.add(circle)
        db.flush()

        membership = CircleMembership(
            circle_id=circle.id,
            user_id=current_user.id,
            pseudonym=current_user.email.split("@")[0],
            role=MemberRole.owner,
        )
        db.add(membership)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
            if attempt == 1:
                raise
    db.refresh(circle)
    return circle


@router.get("/circles/{circle_id}", response_model=CircleOut)
def get_circle(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """Return a single circle by ID. The caller must be a member."""
    circle = get_circle_or_404(db, circle_id)
    get_membership_or_403(db, circle_id, current_user.id)
    return circle


@router.patch("/circles/{circle_id}", response_model=CircleOut)
def update_circle(
    circle_id: uuid.UUID,
    circle_in: CircleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """Update circle settings. Requires owner or admin role."""
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)

    update_data = circle_in.model_dump(exclude_unset=True)
    apply_partial_update(circle, update_data)

    db.commit()
    db.refresh(circle)
    return circle


@router.delete("/circles/{circle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_circle(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Permanently delete a circle. Requires owner role."""
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_owner(membership)
    db.delete(circle)
    db.commit()


def _image_ref(circle_id: uuid.UUID, image: CircleImage) -> str:
    """
    Build the API-relative hero-image URL with a cache-bust version.

    The path is relative to the API base (no host), so the frontend
    resolves it against its configured ``apiBaseUrl``. The ``v``
    query param changes whenever the image is replaced, forcing
    browsers to refetch even though the path is otherwise stable.

    :param circle_id: Owning circle identifier.
    :param image: Persisted image row (``updated_at`` must be set).
    :returns: Path such as ``/circles/<id>/image?v=<epoch>``.
    """
    version = int(image.updated_at.timestamp())
    return f"/circles/{circle_id}/image?v={version}"


@router.post("/circles/{circle_id}/image", response_model=CircleOut)
def upload_circle_image(
    circle_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> Circle:
    """
    Upload (or replace) the circle's hero image. Owner/admin only.

    :raises HTTPException: 400 for an unsupported content type, 413
        when the payload exceeds ``CIRCLE_IMAGE_MAX_BYTES``.
    """
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)

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
        select(CircleImage).where(CircleImage.circle_id == circle_id)
    ).scalar_one_or_none()
    if image is None:
        image = CircleImage(circle_id=circle_id)
        db.add(image)
    image.content_type = content_type
    image.data = data

    db.flush()
    db.refresh(image)
    circle.image_ref = _image_ref(circle_id, image)

    db.commit()
    db.refresh(circle)
    return circle


@router.get("/circles/{circle_id}/image")
def get_circle_image(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    """
    Return the circle's hero image bytes.

    Public (no authentication): the unguessable circle UUID acts as
    the access capability, mirroring the public invite-preview
    endpoint. Responses are cacheable because the caller's URL is
    versioned via the ``v`` query param.

    :raises HTTPException: 404 when the circle has no stored image.
    """
    image = db.execute(
        select(CircleImage).where(CircleImage.circle_id == circle_id)
    ).scalar_one_or_none()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image for this circle",
        )
    return Response(
        content=image.data,
        media_type=image.content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.delete("/circles/{circle_id}/image", response_model=CircleOut)
def delete_circle_image(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """Remove the circle's hero image. Owner/admin only."""
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)

    image = db.execute(
        select(CircleImage).where(CircleImage.circle_id == circle_id)
    ).scalar_one_or_none()
    if image is not None:
        db.delete(image)
    circle.image_ref = None

    db.commit()
    db.refresh(circle)
    return circle


@router.post("/circles/{circle_id}/invite", response_model=CircleOut)
def regenerate_invite(
    circle_id: uuid.UUID,
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(limit_invite_regeneration),
    current_user: User = Depends(get_current_active_user),
) -> Circle:
    """
    Generate a new invite token for *circle_id*, invalidating the
    previous one. Requires owner or admin role.
    """
    circle = get_circle_or_404(db, circle_id)
    membership = get_membership_or_403(db, circle_id, current_user.id)
    require_admin_or_owner(membership)
    for attempt in range(2):
        circle.invite_token = generate_unique_pin(db)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
            if attempt == 1:
                raise
    db.refresh(circle)
    return circle


@router.get("/circles/join/{invite_token}", response_model=CircleOut)
def preview_circle_by_invite(
    invite_token: str,
    db: Session = Depends(get_db),
) -> Circle:
    """
    Return public circle details for a valid *invite_token* without
    requiring authentication.
    """
    circle = db.execute(
        select(Circle).where(Circle.invite_token == normalize_pin(invite_token))
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite PIN"
        )
    return circle


@router.post(
    "/circles/join",
    response_model=MembershipOut,
    status_code=status.HTTP_201_CREATED,
)
def join_circle(
    join_in: InviteJoin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CircleMembership:
    """Join a circle using an invite token and choose a per-circle pseudonym."""
    circle = db.execute(
        select(Circle).where(Circle.invite_token == join_in.invite_token)
    ).scalar_one_or_none()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite PIN"
        )

    existing = db.execute(
        select(CircleMembership).where(
            CircleMembership.circle_id == circle.id,
            CircleMembership.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member"
        )

    # Check pseudonym uniqueness within the circle
    pseudonym_taken = db.execute(
        select(CircleMembership).where(
            CircleMembership.circle_id == circle.id,
            CircleMembership.pseudonym == join_in.pseudonym,
        )
    ).scalar_one_or_none()
    if pseudonym_taken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pseudonym already taken in this circle",
        )

    membership = CircleMembership(
        circle_id=circle.id,
        user_id=current_user.id,
        pseudonym=join_in.pseudonym,
        role=MemberRole.member,
        can_host_default=join_in.can_host_default,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
