"""Daily email digests for service and document reminders."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import func, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.document import Document
from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.utils.dates import app_today
from app.utils.email import send_reminder_digest_email
from app.utils.health import riding_rate_km_per_day
from app.utils.reminders import (
    build_document_reminders,
    build_service_reminder,
    find_active_next_service,
)

logger = logging.getLogger(__name__)

_DIGEST_TTL_SECONDS = 26 * 60 * 60


def window_phrase(days: int) -> str:
    """Bucket remaining days into a rider-facing window, not a countdown."""
    if days <= 0:
        return "now"
    if days <= 6:
        return "within a few days"
    if days <= 10:
        return "within about a week"
    if days <= 17:
        return "within 1–2 weeks"
    if days <= 31:
        return "within a few weeks"
    weeks = max(5, round(days / 7))
    return f"in about {weeks} weeks"


def format_service_digest_line(
    *,
    status: str,
    days_until: int | None,
    km_until: float | None,
    riding_rate_km_per_day: float | None,
) -> str:
    """Service digest line: predicted window, or an honest fallback."""
    if status == "overdue":
        bits: list[str] = []
        if days_until is not None and days_until < 0:
            n = abs(days_until)
            bits.append(f"{n} day{'s' if n != 1 else ''} past due")
        if km_until is not None and km_until < 0:
            km = abs(km_until)
            bits.append(f"{km:g} km past due")
        if bits:
            return "Service overdue — " + "; ".join(bits)
        return "Service overdue"

    days_by_km: int | None = None
    if (
        riding_rate_km_per_day is not None
        and km_until is not None
        and km_until > 0
    ):
        days_by_km = max(0, int(round(km_until / riding_rate_km_per_day)))

    calendar_days = (
        days_until if days_until is not None and days_until >= 0 else None
    )

    if days_by_km is not None and (
        calendar_days is None or days_by_km < calendar_days
    ):
        return (
            "Service soon — likely "
            f"{window_phrase(days_by_km)} at your recent riding"
        )

    if calendar_days is not None:
        extra = ""
        if riding_rate_km_per_day is None:
            extra = " (not enough riding data for a forecast)"
        return (
            "Service soon — due "
            f"{window_phrase(calendar_days)} by the date you set{extra}"
        )

    if km_until is not None and km_until >= 0:
        return (
            f"Service soon — {km_until:g} km left "
            "(not enough riding data to estimate when)"
        )
    return "Service soon"


def format_document_digest_line(
    *,
    display_label: str,
    identifier: str | None,
    status: str,
    days_until: int,
) -> str:
    """Document digest line: windowed expiry, not `soon (12 days)`."""
    name = display_label
    if identifier:
        name = f"{display_label} ({identifier})"
    if status == "expired":
        n = abs(days_until)
        when = "today" if n == 0 else f"{n} day{'s' if n != 1 else ''} ago"
        return f"{name} expired {when}"
    return f"{name} expires {window_phrase(days_until)}"


@dataclass
class DigestResult:
    users_considered: int
    emails_sent: int
    emails_skipped: int


def _digest_key(user_id: uuid.UUID, day: str) -> str:
    return f"reminder:digest:{user_id}:{day}"


async def _live_odometers_map(
    db: AsyncSession,
    vehicles: list[Vehicle],
) -> dict[uuid.UUID, float]:
    if not vehicles:
        return {}

    vehicle_ids = [vehicle.id for vehicle in vehicles]
    baselines = {
        vehicle.id: float(vehicle.current_odometer or 0) for vehicle in vehicles
    }

    fuel_max = (
        select(
            FuelLog.vehicle_id.label("vehicle_id"),
            func.max(FuelLog.odometer).label("odometer"),
        )
        .where(FuelLog.vehicle_id.in_(vehicle_ids))
        .group_by(FuelLog.vehicle_id)
    )
    service_max = (
        select(
            ServiceLog.vehicle_id.label("vehicle_id"),
            func.max(ServiceLog.odometer).label("odometer"),
        )
        .where(ServiceLog.vehicle_id.in_(vehicle_ids))
        .group_by(ServiceLog.vehicle_id)
    )
    combined = union_all(fuel_max, service_max).subquery()
    result = await db.execute(
        select(
            combined.c.vehicle_id,
            func.max(combined.c.odometer),
        ).group_by(combined.c.vehicle_id)
    )
    log_max = {row[0]: float(row[1] or 0) for row in result.all()}

    return {
        vid: max(baselines[vid], log_max.get(vid, 0.0)) for vid in vehicle_ids
    }


async def _claim_digest_slot(redis: Redis, user_id: uuid.UUID, day: str) -> bool:
    """Return True if this is the first claim for the user today (NX)."""
    return bool(
        await redis.set(
            _digest_key(user_id, day),
            b"1",
            nx=True,
            ex=_DIGEST_TTL_SECONDS,
        )
    )


async def send_reminder_digests(
    db: AsyncSession,
    redis: Redis,
) -> DigestResult:
    """
    Email verified users who have soon/overdue service or document reminders.

    Idempotent per user per calendar day via Redis.
    """
    today = app_today()
    day = today.isoformat()
    dashboard_url = f"{settings.FRONTEND_URL.rstrip('/')}/"

    users_result = await db.execute(
        select(User)
        .where(
            User.email_verified.is_(True),
            User.is_active.is_(True),
            or_(
                User.email_service_reminders.is_(True),
                User.email_document_reminders.is_(True),
            ),
        )
        .options(selectinload(User.vehicles))
    )
    users = list(users_result.scalars().unique().all())

    sent = 0
    skipped = 0

    for user in users:
        vehicles = list(user.vehicles)
        if not vehicles:
            skipped += 1
            continue

        include_service = bool(user.email_service_reminders)
        include_documents = bool(user.email_document_reminders)

        live_map = await _live_odometers_map(db, vehicles)
        sections_text: list[str] = []
        sections_html: list[str] = []

        for vehicle in vehicles:
            if vehicle.reminders_muted:
                continue

            vehicle_id = vehicle.id
            live_odo = live_map[vehicle_id]

            needs_service = False
            service_reminder = None
            rate = None
            if include_service:
                service_result = await db.execute(
                    select(ServiceLog)
                    .where(ServiceLog.vehicle_id == vehicle_id)
                    .order_by(ServiceLog.date.desc(), ServiceLog.odometer.desc())
                )
                service_logs = list(service_result.scalars().all())
                next_service = find_active_next_service(service_logs)
                service_reminder = build_service_reminder(
                    next_service,
                    today=today,
                    live_odometer=live_odo,
                )
                needs_service = service_reminder.status in ("soon", "overdue")
                if needs_service:
                    fuel_result = await db.execute(
                        select(FuelLog).where(FuelLog.vehicle_id == vehicle_id)
                    )
                    rate = riding_rate_km_per_day(
                        list(fuel_result.scalars().all())
                    )

            document_reminders = []
            if include_documents:
                docs_result = await db.execute(
                    select(Document)
                    .where(
                        Document.vehicle_id == vehicle_id,
                        Document.expiry_date.is_not(None),
                    )
                    .order_by(Document.expiry_date.asc())
                )
                documents = list(docs_result.scalars().all())
                document_reminders = build_document_reminders(
                    documents, today=today
                )

            if not needs_service and not document_reminders:
                continue

            label = (
                f"{vehicle.brand} {vehicle.vehicle_name}".strip()
                or vehicle.registration_number
            )
            lines: list[str] = [f"{label}:"]
            html_bits: list[str] = [f"<p><strong>{label}</strong></p><ul>"]

            if needs_service and service_reminder is not None:
                detail = format_service_digest_line(
                    status=service_reminder.status,
                    days_until=service_reminder.days_until,
                    km_until=service_reminder.km_until,
                    riding_rate_km_per_day=rate,
                )
                lines.append(f"  - {detail}")
                html_bits.append(f"<li>{detail}</li>")

            for doc in document_reminders:
                detail = format_document_digest_line(
                    display_label=doc.display_label,
                    identifier=doc.identifier,
                    status=doc.status,
                    days_until=doc.days_until,
                )
                lines.append(f"  - {detail}")
                html_bits.append(f"<li>{detail}</li>")

            html_bits.append("</ul>")
            sections_text.append("\n".join(lines))
            sections_html.append("".join(html_bits))

        if not sections_text:
            skipped += 1
            continue

        if not await _claim_digest_slot(redis, user.id, day):
            skipped += 1
            continue

        try:
            await send_reminder_digest_email(
                to=user.email,
                full_name=user.full_name,
                dashboard_url=dashboard_url,
                body_text="\n\n".join(sections_text),
                body_html="".join(sections_html),
            )
        except Exception:
            logger.exception(
                "Failed to send reminder digest to user_id=%s", user.id
            )
            # Release the day claim so a later cron can retry
            await redis.delete(_digest_key(user.id, day))
            skipped += 1
            continue

        sent += 1
        logger.info("Reminder digest sent to user_id=%s", user.id)

    return DigestResult(
        users_considered=len(users),
        emails_sent=sent,
        emails_skipped=skipped,
    )
