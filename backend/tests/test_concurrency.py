"""Concurrency and transaction-boundary tests (roadmap Phase 1)."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.config import settings
from app.utils.cache import vehicle_summary_key
from app.utils.dates import app_today
from app.utils.redis_client import get_redis
from main import app


async def test_concurrent_refresh_same_token_exactly_one_wins(
    client: AsyncClient, registered_user: dict
):
    """Same refresh token used twice concurrently → one 200, one 401."""
    login = await client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert login.status_code == 200
    refresh = login.cookies["refresh_token"]
    client.cookies.clear()

    first, second = await asyncio.gather(
        client.post("/auth/refresh", json={"refresh_token": refresh}),
        client.post("/auth/refresh", json={"refresh_token": refresh}),
    )

    statuses = sorted([first.status_code, second.status_code])
    assert statuses == [200, 401], (
        f"expected exactly one successful rotation, got {statuses}"
    )

    winner = first if first.status_code == 200 else second
    new_refresh = winner.cookies.get("refresh_token")
    assert new_refresh
    assert new_refresh != refresh


async def test_concurrent_fuel_creates_consistent_timeline(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Two overlapping fuel creates must both land with a coherent mileage chain."""
    vehicle_id = created_vehicle["id"]
    today = str(app_today())

    async def create_fill(odometer: int):
        return await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": today,
                "odometer": odometer,
                "total_cost": 500,
                "price_per_liter": 100,
            },
            headers=auth_headers,
        )

    first, second = await asyncio.gather(
        create_fill(10100),
        create_fill(10200),
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    listing = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id, "size": 20},
        headers=auth_headers,
    )
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert len(items) == 2

    # Oldest → newest by odometer (API returns newest first)
    by_odo = sorted(items, key=lambda row: row["odometer"])
    assert by_odo[0]["odometer"] == 10100
    assert by_odo[1]["odometer"] == 10200
    assert by_odo[0]["mileage"] is not None
    assert by_odo[1]["mileage"] is not None
    # Second fill uses the first fill's odometer as previous
    liters_second = by_odo[1]["liters"]
    expected = round((10200 - 10100) / liters_second, 2)
    assert by_odo[1]["mileage"] == expected


async def test_cache_stampede_summary_after_invalidate(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Concurrent summary reads after a write all succeed (no crash / 5xx)."""
    vehicle_id = created_vehicle["id"]

    warm = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert warm.status_code == 200

    fill = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            "odometer": 10500,
            "total_cost": 400,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert fill.status_code == 201

    results = await asyncio.gather(
        *[
            client.get(
                f"/vehicles/{vehicle_id}/summary",
                headers=auth_headers,
            )
            for _ in range(5)
        ]
    )
    assert all(response.status_code == 200 for response in results)
    counts = {response.json()["fuel_log_count"] for response in results}
    assert counts == {1}


async def test_fuel_create_rollback_leaves_cache_untouched_on_validation_error(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Failed fuel create must not wipe a warm summary cache."""
    vehicle_id = created_vehicle["id"]

    warm = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert warm.status_code == 200
    assert warm.json()["fuel_log_count"] == 0

    redis = app.dependency_overrides[get_redis]()
    cache_key = vehicle_summary_key(vehicle_id)
    assert await redis.get(cache_key) is not None

    bad = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            # At or below baseline → validation failure during recalc
            "odometer": created_vehicle["current_odometer"],
            "total_cost": 400,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert bad.status_code == 400

    # Cache from the warm hit should still be present (invalidation only on success)
    assert await redis.get(cache_key) is not None

    again = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert again.status_code == 200
    assert again.json()["fuel_log_count"] == 0


async def test_concurrent_digest_cron_sends_at_most_one_email(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
    monkeypatch,
):
    """Two overlapping digest cron posts → at most one email (Redis NX claim)."""
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "test-cron-secret")
    send_mock = AsyncMock()
    monkeypatch.setattr(
        "app.utils.reminder_digest.send_reminder_digest_email",
        send_mock,
    )

    vehicle_id = created_vehicle["id"]
    today = app_today()
    service = await client.post(
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
    assert service.status_code == 201, service.text

    first, second = await asyncio.gather(
        client.post(
            "/internal/reminder-digests",
            headers={"X-Cron-Secret": "test-cron-secret"},
        ),
        client.post(
            "/internal/reminder-digests",
            headers={"X-Cron-Secret": "test-cron-secret"},
        ),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    total_sent = first.json()["emails_sent"] + second.json()["emails_sent"]
    assert total_sent == 1
    assert send_mock.await_count == 1
