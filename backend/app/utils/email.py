"""Transactional email via Resend (HTTPS) or SMTP. Without either, logs the body."""

import logging
from email.message import EmailMessage

import aiosmtplib
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


async def _send_via_resend(*, to: str, subject: str, html: str, text: str) -> None:
    """Send over HTTPS — works on Render free (SMTP ports are blocked)."""
    payload = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
        "text": text,
    }
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(_RESEND_URL, json=payload, headers=headers)
    if response.status_code >= 400:
        logger.error(
            "Resend failed status=%s body=%s",
            response.status_code,
            response.text,
        )
        response.raise_for_status()
    logger.info("Email sent via Resend to=%s subject=%s", to, subject)


async def _send_via_smtp(*, to: str, subject: str, html: str, text: str) -> None:
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=settings.SMTP_STARTTLS,
    )
    logger.info("Email sent via SMTP to=%s subject=%s", to, subject)


async def send_email(*, to: str, subject: str, html: str, text: str) -> None:
    """
    Send email. Prefer Resend when RESEND_API_KEY is set (Render-safe).
    Else SMTP when SMTP_HOST is set. Else log the body (dev/test).
    """
    if settings.RESEND_API_KEY:
        await _send_via_resend(to=to, subject=subject, html=html, text=text)
        return

    if not settings.SMTP_HOST:
        logger.warning(
            "Email NOT sent — set RESEND_API_KEY (recommended on Render) "
            "or SMTP_HOST in .env. to=%s subject=%s\n%s",
            to,
            subject,
            text,
        )
        return

    await _send_via_smtp(to=to, subject=subject, html=html, text=text)


async def send_verification_email(*, to: str, full_name: str, link: str) -> None:
    subject = "Verify your RideCare email"
    text = (
        f"Hi {full_name},\n\n"
        f"Confirm your RideCare account:\n{link}\n\n"
        f"This link expires in {settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS} hours.\n"
        "If you did not sign up, you can ignore this email.\n"
    )
    html = (
        f"<p>Hi {full_name},</p>"
        f"<p>Confirm your RideCare account:</p>"
        f'<p><a href="{link}">Verify email</a></p>'
        f"<p>This link expires in {settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS} hours.</p>"
        "<p>If you did not sign up, you can ignore this email.</p>"
    )
    await send_email(to=to, subject=subject, html=html, text=text)


async def send_password_reset_email(*, to: str, full_name: str, link: str) -> None:
    subject = "Reset your RideCare password"
    hours = settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    text = (
        f"Hi {full_name},\n\n"
        f"Reset your RideCare password:\n{link}\n\n"
        f"This link expires in {hours} hour{'s' if hours != 1 else ''}.\n"
        "If you did not request a reset, you can ignore this email.\n"
    )
    html = (
        f"<p>Hi {full_name},</p>"
        f"<p>Reset your RideCare password:</p>"
        f'<p><a href="{link}">Choose a new password</a></p>'
        f"<p>This link expires in {hours} hour{'s' if hours != 1 else ''}.</p>"
        "<p>If you did not request a reset, you can ignore this email.</p>"
    )
    await send_email(to=to, subject=subject, html=html, text=text)


async def send_reminder_digest_email(
    *,
    to: str,
    full_name: str,
    dashboard_url: str,
    body_text: str,
    body_html: str,
) -> None:
    subject = "RideCare reminders"
    text = (
        f"Hi {full_name},\n\n"
        f"{body_text}\n\n"
        f"Open your garage: {dashboard_url}\n"
    )
    html = (
        f"<p>Hi {full_name},</p>"
        f"{body_html}"
        f'<p><a href="{dashboard_url}">Open RideCare</a></p>'
    )
    await send_email(to=to, subject=subject, html=html, text=text)
