"""Email transport unit tests (Brevo preferred over SMTP)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.config import settings
from app.utils.email import _parse_from_address, send_email


def test_parse_from_address_with_display_name():
    assert _parse_from_address('RideCare <you@gmail.com>') == (
        "RideCare",
        "you@gmail.com",
    )


def test_parse_from_address_bare_email():
    assert _parse_from_address("you@gmail.com") == ("RideCare", "you@gmail.com")


@pytest.mark.asyncio
async def test_send_email_uses_brevo_when_api_key_set(monkeypatch):
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib-test")
    monkeypatch.setattr(settings, "EMAIL_FROM", "RideCare <you@gmail.com>")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.utils.email.httpx.AsyncClient", return_value=mock_client):
        with patch("app.utils.email.aiosmtplib.send", new_callable=AsyncMock) as smtp:
            await send_email(
                to="rider@example.com",
                subject="Hello",
                html="<p>Hi</p>",
                text="Hi",
            )
            smtp.assert_not_awaited()

    mock_client.post.assert_awaited_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "https://api.brevo.com/v3/smtp/email"
    assert kwargs["headers"]["api-key"] == "xkeysib-test"
    assert kwargs["json"]["to"] == [{"email": "rider@example.com"}]
    assert kwargs["json"]["sender"] == {
        "name": "RideCare",
        "email": "you@gmail.com",
    }


@pytest.mark.asyncio
async def test_send_email_raises_on_brevo_error(monkeypatch):
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib-test")

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "forbidden"
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "forbidden",
            request=MagicMock(),
            response=mock_response,
        )
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.utils.email.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await send_email(
                to="rider@example.com",
                subject="Hello",
                html="<p>Hi</p>",
                text="Hi",
            )
