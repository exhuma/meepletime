"""Render notification & confirmation emails as HTML + plain text.

Control flow (per-event-type wording, the loop over batch days, and the
hero image vs. gradient fallback) lives here in stdlib Python; the
bundled files under ``templates/`` are pure :class:`string.Template`
shells generated from the frontend design tokens (see
``frontend/email/build.ts``). The plain-text alternative is kept
byte-for-byte identical to the previous plain-text emails so subscribers
see no regression.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from string import Template

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.circle_image import CircleImage
from app.services.notifications.context import EventContext

# Inline images larger than this are skipped (uploads can be several
# MB); the gradient hero is used instead to avoid bloated emails.
MAX_INLINE_IMAGE_BYTES = 512 * 1024

# Package holding the bundled, generated template files.
_PKG = "app.services.notifications"


@dataclass
class RenderedEmail:
    """A rendered email in both HTML and plain-text form.

    :param html: The HTML alternative.
    :param text: The plain-text alternative.
    :param image: Optional inline hero as ``(data, content_type)``.
    """

    html: str
    text: str
    image: tuple[bytes, str] | None


@cache
def _template(name: str) -> Template:
    """
    Load and cache one bundled template.

    :param name: Template file name, e.g. ``shell.html``.
    :returns: A parsed :class:`string.Template`.
    """
    text = files(_PKG).joinpath("templates", name).read_text(encoding="utf-8")
    return Template(text)


def _initials(name: str) -> str:
    """
    Derive at-most-two-letter initials, mirroring the frontend.

    See ``CirclesView.initials``: first two characters, uppercased.

    :param name: The circle (or brand) name.
    :returns: One or two uppercase characters.
    """
    return name.strip()[:2].upper()


def _hero(
    name: str, image: CircleImage | None
) -> tuple[str, tuple[bytes, str] | None]:
    """
    Build the hero block and any inline-image payload.

    :param name: Circle/brand name (alt text and initials fallback).
    :param image: The circle's stored image row, if any.
    :returns: ``(hero_html, image_or_None)``.
    """
    if image is not None and len(image.data) <= MAX_INLINE_IMAGE_BYTES:
        hero = _template("hero_image.html").substitute(
            alt=html.escape(name, quote=True)
        )
        return hero, (image.data, image.content_type)
    hero = _template("hero_fallback.html").substitute(
        initials=html.escape(_initials(name))
    )
    return hero, None


def _shell(preheader: str, hero: str, content: str) -> str:
    """
    Wrap a hero block and body content in the outer document shell.

    :param preheader: Hidden inbox-preview text.
    :param hero: Pre-rendered hero block HTML.
    :param content: Pre-rendered body HTML.
    :returns: The full HTML document.
    """
    return _template("shell.html").substitute(
        preheader=html.escape(preheader),
        hero=hero,
        content=content,
    )


def _day_list(lines: list[str]) -> str:
    """
    Render the batch day rows from the plain-text body lines.

    Each line has the form ``- <date>: <phrase>`` (see
    :func:`build_batch_context`); non-matching lines are ignored.

    :param lines: Body lines following the summary header line.
    :returns: HTML for the day-list table.
    """
    row = _template("day_row.html")
    rows: list[str] = []
    for line in lines:
        item = line.strip()
        if not item.startswith("- "):
            continue
        day, sep, phrase = item[2:].partition(": ")
        if not sep:
            day, phrase = item[2:], ""
        rows.append(
            row.substitute(day=html.escape(day), phrase=html.escape(phrase))
        )
    return _template("day_list.html").substitute(rows="".join(rows))


def render_notification(ctx: EventContext, db: Session) -> RenderedEmail:
    """
    Render a viability notification email.

    :param ctx: The event context being delivered.
    :param db: Active database session (used to load the hero image).
    :returns: The rendered HTML + plain-text email.
    """
    text = f"{ctx.body}\n\n{ctx.url}\n"
    image = db.execute(
        select(CircleImage).where(CircleImage.circle_id == ctx.circle_id)
    ).scalar_one_or_none()
    hero, payload = _hero(ctx.circle_name, image)

    if ctx.event_type == "batch":
        lines = ctx.body.split("\n")
        lead = lines[0]
        detail = _day_list(lines[1:])
        cta_label = "View circle"
    else:
        lead = ctx.body
        detail = ""
        cta_label = "View this day"

    content = _template("notification_body.html").substitute(
        heading=html.escape(ctx.title),
        lead=html.escape(lead),
        detail=detail,
        cta_url=html.escape(ctx.url, quote=True),
        cta_label=cta_label,
    )
    return RenderedEmail(
        html=_shell(ctx.title, hero, content), text=text, image=payload
    )


def render_confirmation(link: str, hours: int, text: str) -> RenderedEmail:
    """
    Render the notification-email confirmation message.

    :param link: The confirmation link to embed in the CTA.
    :param hours: Validity window, in hours, for the wording.
    :param text: The exact plain-text body (kept byte-for-byte).
    :returns: The rendered HTML + plain-text email.
    """
    hero, _ = _hero("MeepleTime", None)
    content = _template("confirmation_body.html").substitute(
        heading="Confirm your email",
        lead=("Confirm this address to receive MeepleTime notifications here."),
        cta_url=html.escape(link, quote=True),
        cta_label="Confirm email",
        note=(
            f"This link is valid for {hours} hours. If you did not "
            "request this, you can ignore this email."
        ),
    )
    return RenderedEmail(
        html=_shell("Confirm your MeepleTime email", hero, content),
        text=text,
        image=None,
    )
