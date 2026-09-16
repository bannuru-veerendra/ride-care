"""RideCare Health API — ranked signals + recommended action."""

from datetime import timedelta

from httpx import AsyncClient

from app.utils.dates import app_today


async def test_health_empty_bike_recommends_thin_history(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        f"/vehicles/{vehicle_id}/health",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == vehicle_id
    assert data["reminders_muted"] is False
    assert data["recommended_action"]["kind"] == "thin_history"
    assert data["service_prediction"]["source"] == "insufficient"
    assert data["mileage"]["trend"] == "insufficient"
    assert data["cost"]["confidence"] == "insufficient"
    kinds = {s["kind"] for s in data["signals"]}
    assert "thin_history" in kinds


async def test_health_service_overdue_is_top_action(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    today = app_today()
    overdue = today - timedelta(days=3)

    service = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today - timedelta(days=30)),
            "odometer": 10500,
            "services_done": ["Engine oil"],
            "total_cost": 500,
            "next_service_date": str(overdue),
            "next_service_odometer": None,
        },
        headers=auth_headers,
    )
    assert service.status_code == 201, service.text

    response = await client.get(
        f"/vehicles/{vehicle_id}/health",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_action"]["kind"] == "service_overdue"
    assert data["recommended_action"]["urgency"] == "critical"
    assert data["service_prediction"]["source"] == "rider_schedule"
    assert data["service_prediction"]["days_until"] == -3


async def test_health_respects_reminders_muted(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    today = app_today()

    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today - timedelta(days=10)),
            "odometer": 11000,
            "services_done": ["Engine oil"],
            "total_cost": 400,
            "next_service_date": str(today - timedelta(days=1)),
            "next_service_odometer": None,
        },
        headers=auth_headers,
    )

    mute = await client.patch(
        f"/vehicles/{vehicle_id}",
        json={"reminders_muted": True},
        headers=auth_headers,
    )
    assert mute.status_code == 200

    response = await client.get(
        f"/vehicles/{vehicle_id}/health",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reminders_muted"] is True
    # Mute suppresses service nags; thin history can still be the next tip (no fuel yet).
    assert data["recommended_action"]["kind"] != "service_overdue"
    assert data["recommended_action"]["kind"] in {"thin_history", "all_clear"}
    assert all(
        s["kind"] not in {"service_overdue", "service_soon"}
        for s in data["signals"]
    )
    # Schedule facts still available via prediction.
    assert data["service_prediction"]["source"] == "rider_schedule"


async def test_health_document_expired_signal(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
):
    vehicle_id = created_vehicle["id"]
    today = app_today()
    expired = today - timedelta(days=5)

    upload = await client.post(
        "/documents/",
        params={"vehicle_id": vehicle_id},
        data={
            "document_type": "insurance",
            "expiry_date": str(expired),
            "identifier": "POL-X",
        },
        files={"file": ("ins.pdf", b"%PDF-1.4 fake", "application/pdf")},
        headers=auth_headers,
    )
    assert upload.status_code == 201, upload.text

    # Enough fuel so thin_history is not the top action.
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

    response = await client.get(
        f"/vehicles/{vehicle_id}/health",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_action"]["kind"] == "document_expired"
    doc_signals = [s for s in data["signals"] if s["kind"] == "document_expired"]
    assert len(doc_signals) == 1
    assert "POL-X" in {e["value"] for e in doc_signals[0]["evidence"]}


async def test_health_not_found_for_other_user(
    client: AsyncClient,
    created_vehicle: dict,
    other_user_headers: dict,
):
    response = await client.get(
        f"/vehicles/{created_vehicle['id']}/health",
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_health_cost_confidence_grows_with_history(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    today = app_today()

    for i in range(5):
        response = await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": str(today - timedelta(days=60 - i * 10)),
                "odometer": 10100 + i * 150,
                "price_per_liter": 105,
                "total_cost": 525,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201, response.text

    health = await client.get(
        f"/vehicles/{vehicle_id}/health",
        headers=auth_headers,
    )
    assert health.status_code == 200
    data = health.json()
    assert data["cost"]["fill_ups"] == 5
    assert data["cost"]["km_driven"] > 0
    assert data["cost"]["cost_per_km"] is not None
    assert data["cost"]["confidence"] in ("low", "medium", "high")
