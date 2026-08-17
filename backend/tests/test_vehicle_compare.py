"""Tests for GET /vehicles/compare."""

from httpx import AsyncClient

from app.utils.dates import app_today


async def test_compare_empty_garage_unauthenticated(client: AsyncClient):
    """Compare requires authentication."""
    response = await client.get("/vehicles/compare")
    assert response.status_code == 401


async def test_compare_single_vehicle_zeroed(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """A bike with no logs still appears, with null cost-per-km."""
    response = await client.get("/vehicles/compare", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["vehicle_id"] == created_vehicle["id"]
    assert item["vehicle_name"] == created_vehicle["vehicle_name"]
    assert item["fuel_spend"] == 0
    assert item["service_spend"] == 0
    assert item["combined_spend"] == 0
    assert item["km_driven"] == 0
    assert item["cost_per_km"] is None
    assert item["fill_up_count"] == 0
    assert item["service_count"] == 0
    assert item["avg_mileage"] is None


async def test_compare_two_vehicles_side_by_side(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Compare returns both bikes with fuel+service cost-per-km."""
    today = app_today()
    first_id = created_vehicle["id"]

    fuel_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": first_id},
        json={
            "date": str(today),
            "odometer": 10500,
            "total_cost": 500,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert fuel_resp.status_code == 201

    service_resp = await client.post(
        "/service_logs/",
        params={"vehicle_id": first_id},
        json={
            "date": str(today),
            "odometer": 10500,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert service_resp.status_code == 201

    second = await client.post(
        "/vehicles/",
        json={
            "brand": "Yamaha",
            "vehicle_name": "MT-15",
            "year": 2022,
            "registration_number": "KA09MT1500",
            "baseline_odometer": 2000,
        },
        headers=auth_headers,
    )
    assert second.status_code == 201
    second_id = second.json()["id"]

    second_fuel = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": second_id},
        json={
            "date": str(today),
            "odometer": 2500,
            "total_cost": 400,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert second_fuel.status_code == 201

    response = await client.get("/vehicles/compare", headers=auth_headers)
    assert response.status_code == 200
    items = {item["vehicle_id"]: item for item in response.json()["items"]}
    assert set(items) == {first_id, second_id}

    first = items[first_id]
    assert first["km_driven"] == 500
    assert first["combined_spend"] == 2000
    assert first["cost_per_km"] == 4.0
    assert first["fill_up_count"] == 1
    assert first["service_count"] == 1

    yamaha = items[second_id]
    assert yamaha["vehicle_name"] == "MT-15"
    assert yamaha["km_driven"] == 500
    assert yamaha["fuel_spend"] == 400
    assert yamaha["service_spend"] == 0
    assert yamaha["combined_spend"] == 400
    assert yamaha["cost_per_km"] == 0.8
    assert yamaha["service_count"] == 0


async def test_compare_hides_other_users_vehicles(
    client: AsyncClient,
    auth_headers: dict,
    other_user_headers: dict,
    created_vehicle: dict,
):
    """Compare is scoped to the authenticated owner's garage."""
    mine = await client.get("/vehicles/compare", headers=auth_headers)
    theirs = await client.get("/vehicles/compare", headers=other_user_headers)
    assert mine.status_code == 200
    assert theirs.status_code == 200
    assert created_vehicle["id"] in [
        item["vehicle_id"] for item in mine.json()["items"]
    ]
    assert theirs.json()["items"] == []
