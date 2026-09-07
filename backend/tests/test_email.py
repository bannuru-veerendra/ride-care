"""Email transport unit tests (Resend preferred over SMTP)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.config import settings
from app.utils.email import send_email


@pytest.mark.asyncio
async def test_send_email_uses_resend_when_api_key_set(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")
    monkeypatch.setattr(settings, "EMAIL_FROM", "RideCare <onboarding@resend.dev>")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")

    mock_response = MagicMock()
    mock_response.status_code = 200
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
    assert args[0] == "https://api.resend.com/emails"
    assert kwargs["headers"]["Authorization"] == "Bearer re_test_key"
    assert kwargs["json"]["to"] == ["rider@example.com"]


@pytest.mark.asyncio
async def test_send_email_raises_on_resend_error(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")

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
