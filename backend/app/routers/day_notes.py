import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_db
from app.models.circle import Circle
from app.models.day_note import DayNote
from app.models.membership import CircleMembership
from app.models.user import User
from app.schemas.day_note import DayNoteCreate, DayNoteOut

router = APIRouter(tags=["day_notes"])


def _get_circle_or_404(db: Session, circle_id: uuid.UUID) -> Circle:
    circle = db.query(Circle).filter(Circle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found")
    return circle


def _require_membership(db: Session, circle_id: uuid.UUID, user_id: uuid.UUID) -> CircleMembership:
    m = (
        db.query(CircleMembership)
        .filter(CircleMembership.circle_id == circle_id, CircleMembership.user_id == user_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this circle")
    return m


def _enrich_note(note: DayNote, db: Session) -> DayNoteOut:
    membership = (
        db.query(CircleMembership)
        .filter(
            CircleMembership.circle_id == note.circle_id,
            CircleMembership.user_id == note.user_id,
        )
        .first()
    )
    pseudonym = membership.pseudonym if membership else None
    out = DayNoteOut.model_validate(note)
    out.pseudonym = pseudonym
    return out


@router.get("/circles/{circle_id}/notes/{local_date}", response_model=list[DayNoteOut])
def list_notes(
    circle_id: uuid.UUID,
    local_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _get_circle_or_404(db, circle_id)
    _require_membership(db, circle_id, current_user.id)

    notes = (
        db.query(DayNote)
        .filter(DayNote.circle_id == circle_id, DayNote.local_date == local_date)
        .order_by(DayNote.created_at)
        .all()
    )
    return [_enrich_note(n, db) for n in notes]


@router.post(
    "/circles/{circle_id}/notes/{local_date}",
    response_model=DayNoteOut,
    status_code=status.HTTP_201_CREATED,
)
def add_note(
    circle_id: uuid.UUID,
    local_date: date,
    note_in: DayNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _get_circle_or_404(db, circle_id)
    _require_membership(db, circle_id, current_user.id)

    note = DayNote(
        circle_id=circle_id,
        user_id=current_user.id,
        local_date=local_date,
        content=note_in.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _enrich_note(note, db)
