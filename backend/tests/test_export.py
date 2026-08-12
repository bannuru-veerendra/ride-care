"""Tests for fuel / service CSV export endpoints."""

from datetime import date, timedelta

from httpx import AsyncClient


async def test_export_fuel_logs_csv(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Fuel export returns CSV with header + fill-up rows."""
    vehicle_id = created_vehicle["id"]
    for i in range(2):
        await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": str(date.today() - timedelta(days=1 - i)),
                "odometer": 10100 + (i * 100),
                "total_cost": 500,
                "price_per_liter": 100,
                "notes": f"fill-{i}",
            },
            headers=auth_headers,
        )

    response = await client.get(
        "/fuel_logs/export",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    body = response.text.lstrip("\ufeff")
    lines = [line for line in body.strip().splitlines() if line]
    assert lines[0].startswith("date,odometer_km,liters")
    assert len(lines) == 3  # header + 2 rows
    assert "fill-1" in body or "fill-0" in body


async def test_export_fuel_logs_empty_csv(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Empty garage still downloads a header-only CSV."""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        "/fuel_logs/export",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.text.lstrip("\ufeff")
    lines = [line for line in body.strip().splitlines() if line]
    assert len(lines) == 1
    assert "odometer_km" in lines[0]


async def test_export_service_logs_csv(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Service export returns CSV including services_done."""
    vehicle_id = created_vehicle["id"]
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 10500,
            "total_cost": 1200,
            "services_done": ["oil_change", "chain_lube"],
            "service_center": "Local garage",
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/service_logs/export",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    body = response.text.lstrip("\ufeff")
    assert "services_done" in body
    assert "oil_change; chain_lube" in body
    assert "Local garage" in body


async def test_export_fuel_logs_requires_auth(
    client: AsyncClient, created_vehicle: dict
):
    response = await client.get(
        "/fuel_logs/export",
        params={"vehicle_id": created_vehicle["id"]},
    )
    assert response.status_code == 401


async def test_export_fuel_logs_forbidden_other_user(
    client: AsyncClient,
    other_user_headers: dict,
    created_vehicle: dict,
):
    """Other users cannot export another rider's fuel history."""
    response = await client.get(
        "/fuel_logs/export",
        params={"vehicle_id": created_vehicle["id"]},
        headers=other_user_headers,
    )
    assert response.status_code == 404
