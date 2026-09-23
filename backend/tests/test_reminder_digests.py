"""Internal reminder digest endpoint tests."""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.config import settings
from app.utils.dates import app_today
from app.utils.reminder_digest import (
    format_document_digest_line,
    format_service_digest_line,
    window_phrase,
)


@pytest.fixture
def cron_secret(monkeypatch):
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "test-cron-secret")
    return "test-cron-secret"


def test_window_phrase_buckets_days():
    assert window_phrase(0) == "now"
    assert window_phrase(5) == "within a few days"
    assert window_phrase(14) == "within 1–2 weeks"
    assert window_phrase(28) == "within a few weeks"


def test_format_service_digest_usage_aware_window():
    line = format_service_digest_line(
        status="soon",
        days_until=None,
        km_until=300,
        riding_rate_km_per_day=20,
    )
    assert line == (
        "Service soon — likely within 1–2 weeks at your recent riding"
    )


def test_format_service_digest_honest_fallback_without_riding_rate():
    line = format_service_digest_line(
        status="soon",
        days_until=5,
        km_until=None,
        riding_rate_km_per_day=None,
    )
    assert "not enough riding data for a forecast" in line
    assert "5 days" not in line
    assert " · " not in line


def test_format_service_digest_overdue_is_not_a_prediction():
    line = format_service_digest_line(
        status="overdue",
        days_until=-3,
        km_until=None,
        riding_rate_km_per_day=20,
    )
    assert line == "Service overdue — 3 days past due"
    assert "likely" not in line


def test_format_document_digest_window():
    soon = format_document_digest_line(
        display_label="Insurance",
        identifier="POL-X",
        status="soon",
        days_until=12,
    )
    assert soon == "Insurance (POL-X) expires within 1–2 weeks"
    expired = format_document_digest_line(
        display_label="Pollution",
        identifier=None,
        status="expired",
        days_until=-4,
    )
    assert expired == "Pollution expired 4 days ago"


async def test_reminder_digests_disabled_without_secret(client: AsyncClient):
    response = await client.post("/internal/reminder-digests")
    assert response.status_code == 503


async def test_reminder_digests_rejects_bad_secret(
    client: AsyncClient, cron_secret: str
):
    response = await client.post(
        "/internal/reminder-digests",
        headers={"X-Cron-Secret": "wrong"},
    )
    assert response.status_code == 401


async def test_reminder_digests_sends_for_soon_service(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
    cron_secret: str,
    monkeypatch,
):
    send_mock = AsyncMock()
    monkeypatch.setattr(
        "app.utils.reminder_digest.send_reminder_digest_email",
        send_mock,
    )

    vehicle_id = created_vehicle["id"]
    today = app_today()
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
            "next_service_date": str(today + timedelta(days=5)),
        },
        headers=auth_headers,
    )

    response = await client.post(
        "/internal/reminder-digests",
        headers={"X-Cron-Secret": cron_secret},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["emails_sent"] >= 1
    assert send_mock.await_count >= 1
    body_text = send_mock.await_args.kwargs["body_text"]
    assert "not enough riding data for a forecast" in body_text
    assert "due within a few days by the date you set" in body_text
    assert " · " not in body_text

    # Second call same day is deduped
    response2 = await client.post(
        "/internal/reminder-digests",
        headers={"X-Cron-Secret": cron_secret},
    )
    assert response2.status_code == 200
    assert response2.json()["emails_sent"] == 0


async def test_reminder_digests_skips_when_prefs_off(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
    cron_secret: str,
    monkeypatch,
):
    send_mock = AsyncMock()
    monkeypatch.setattr(
        "app.utils.reminder_digest.send_reminder_digest_email",
        send_mock,
    )

    await client.patch(
        "/users/me",
        json={
            "email_service_reminders": False,
            "email_document_reminders": False,
        },
        headers=auth_headers,
    )

    vehicle_id = created_vehicle["id"]
    today = app_today()
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
            "next_service_date": str(today + timedelta(days=5)),
        },
        headers=auth_headers,
    )

    response = await client.post(
        "/internal/reminder-digests",
        headers={"X-Cron-Secret": cron_secret},
    )
    assert response.status_code == 200
    assert response.json()["emails_sent"] == 0
    assert send_mock.await_count == 0


async def test_reminder_digests_skips_muted_vehicle(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
    cron_secret: str,
    monkeypatch,
):
    send_mock = AsyncMock()
    monkeypatch.setattr(
        "app.utils.reminder_digest.send_reminder_digest_email",
        send_mock,
    )

    vehicle_id = created_vehicle["id"]
    today = app_today()
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today),
            "odometer": 12000.5,
            "total_cost": 1500.25,
            "services_done": ["Engine oil"],
            "next_service_date": str(today + timedelta(days=5)),
        },
        headers=auth_headers,
    )
    mute = await client.patch(
        f"/vehicles/{vehicle_id}",
        json={"reminders_muted": True},
        headers=auth_headers,
    )
    assert mute.status_code == 200

    response = await client.post(
        "/internal/reminder-digests",
        headers={"X-Cron-Secret": cron_secret},
    )
    assert response.status_code == 200
    assert response.json()["emails_sent"] == 0
    assert send_mock.await_count == 0


async def test_reminder_digests_uses_riding_rate_window(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
    cron_secret: str,
    monkeypatch,
):
    send_mock = AsyncMock()
    monkeypatch.setattr(
        "app.utils.reminder_digest.send_reminder_digest_email",
        send_mock,
    )

    vehicle_id = created_vehicle["id"]
    today = app_today()
    for i in range(3):
        fuel = await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": str(today - timedelta(days=40 - i * 10)),
                "odometer": 10100 + i * 200,
                "price_per_liter": 100,
                "total_cost": 500,
            },
            headers=auth_headers,
        )
        assert fuel.status_code == 201, fuel.text

    service = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
            "next_service_odometer": 12300,
        },
        headers=auth_headers,
    )
    assert service.status_code == 201, service.text

    response = await client.post(
        "/internal/reminder-digests",
        headers={"X-Cron-Secret": cron_secret},
    )
    assert response.status_code == 200
    assert response.json()["emails_sent"] >= 1
    body_text = send_mock.await_args.kwargs["body_text"]
    assert "likely within 1–2 weeks at your recent riding" in body_text
    assert "300 km" not in body_text


async def test_suggest_next_due_endpoint(
    client: AsyncClient, auth_headers: dict
):
    response = await client.post(
        "/service_logs/suggest-next-due",
        json={
            "date": "2026-01-15",
            "odometer": 10000,
            "services_done": ["Engine Oil"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["next_service_odometer"] == 13000
    assert data["next_service_date"] == "2026-04-15"
    assert "Engine oil change" in data["matched_tasks"]
