from datetime import date

from httpx import AsyncClient


async def test_create_vehicle_success(client: AsyncClient, auth_headers: dict):
    """Test the create vehicle endpoint"""
    payload = {
        "brand": "Honda",
        "vehicle_name": "Shine 100",
        "year": 2022,
        "registration_number": "TS09CD5678",
        "baseline_odometer": 3000,
    }
    response = await client.post("/vehicles/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["brand"] == payload["brand"]
    assert data["registration_number"] == payload["registration_number"]
    assert data["baseline_odometer"] == 3000
    assert data["current_odometer"] == 3000
    assert "id" in data
    assert "owner_id" in data


async def test_create_vehicle_accepts_legacy_current_odometer(
    client: AsyncClient, auth_headers: dict
):
    """Legacy create payloads may still send current_odometer as baseline."""
    payload = {
        "brand": "TVS",
        "vehicle_name": "Apache",
        "year": 2021,
        "registration_number": "TS09LEGACY1",
        "current_odometer": 4500,
    }
    response = await client.post("/vehicles/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["baseline_odometer"] == 4500
    assert data["current_odometer"] == 4500


async def test_create_vehicle_duplicate_registration(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test the create vehicle endpoint with a duplicate registration number"""
    payload = {
        "brand": "Bajaj",
        "vehicle_name": "Pulsar 150",
        "year": 2021,
        "registration_number": created_vehicle["registration_number"],
        "baseline_odometer": 0,
    }
    response = await client.post("/vehicles/", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


async def test_update_vehicle_duplicate_registration(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test the update vehicle endpoint with a duplicate registration number"""
    create_response = await client.post(
        "/vehicles/",
        json={
            "brand": "Bajaj",
            "vehicle_name": "Pulsar 150",
            "year": 2021,
            "registration_number": "TS09EF9012",
            "baseline_odometer": 0,
        },
        headers=auth_headers,
    )
    vehicle_id = create_response.json()["id"]

    response = await client.patch(
        f"/vehicles/{vehicle_id}",
        json={"registration_number": created_vehicle["registration_number"]},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


async def test_create_vehicle_invalid_year(client: AsyncClient, auth_headers: dict):
    """Test the create vehicle endpoint with an invalid year"""
    payload = {
        "brand": "Honda",
        "vehicle_name": "Shine 100",
        "year": 1885,
        "registration_number": "TS09CD5678",
        "baseline_odometer": 3000,
    }
    response = await client.post("/vehicles/", json=payload, headers=auth_headers)
    assert response.status_code == 422


async def test_create_vehicle_negative_odometer(client: AsyncClient, auth_headers: dict):
    """Test the create vehicle endpoint with a negative odometer"""
    payload = {
        "brand": "Honda",
        "vehicle_name": "Shine 100",
        "year": 2022,
        "registration_number": "TS09CD5678",
        "baseline_odometer": -1,
    }
    response = await client.post("/vehicles/", json=payload, headers=auth_headers)
    assert response.status_code == 422


async def test_get_vehicles_empty(client: AsyncClient, auth_headers: dict):
    """Test the get vehicles endpoint returns an empty list when none exist"""
    response = await client.get("/vehicles/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_get_vehicles(client: AsyncClient, auth_headers: dict, created_vehicle: dict):
    """Test the get vehicles endpoint"""
    response = await client.get("/vehicles/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == created_vehicle["id"]


async def test_get_vehicle_by_id(client: AsyncClient, auth_headers: dict, created_vehicle: dict):
    """Test the get vehicle by id endpoint"""
    vehicle_id = created_vehicle["id"]
    response = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == vehicle_id


async def test_get_vehicle_not_found(client: AsyncClient, auth_headers: dict):
    """Test the get vehicle by id endpoint with a non-existent id"""
    vehicle_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert response.status_code == 404


async def test_update_vehicle(client: AsyncClient, auth_headers: dict, created_vehicle: dict):
    """Test the update vehicle endpoint"""
    vehicle_id = created_vehicle["id"]
    payload = {"baseline_odometer": 6000}
    response = await client.patch(f"/vehicles/{vehicle_id}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["baseline_odometer"] == 6000
    assert response.json()["current_odometer"] == 6000


async def test_update_vehicle_not_found(client: AsyncClient, auth_headers: dict):
    """Test the update vehicle endpoint with a non-existent id"""
    vehicle_id = "00000000-0000-0000-0000-000000000000"
    payload = {"baseline_odometer": 6000}
    response = await client.patch(f"/vehicles/{vehicle_id}", json=payload, headers=auth_headers)
    assert response.status_code == 404


async def test_current_odometer_follows_fuel_and_service_logs(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Live current_odometer advances from fuel/service logs; baseline stays fixed."""
    vehicle_id = created_vehicle["id"]
    baseline = created_vehicle["baseline_odometer"]

    await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 11200,
            "total_cost": 800,
            "price_per_liter": 110,
        },
        headers=auth_headers,
    )
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )

    response = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["baseline_odometer"] == baseline
    assert data["current_odometer"] == 12000


async def test_update_baseline_rejects_value_at_or_above_logs(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Baseline cannot be raised to or above existing log odometers."""
    vehicle_id = created_vehicle["id"]
    await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 11200,
            "total_cost": 800,
            "price_per_liter": 110,
        },
        headers=auth_headers,
    )

    response = await client.patch(
        f"/vehicles/{vehicle_id}",
        json={"baseline_odometer": 11200},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "baseline odometer" in response.json()["detail"].lower()


async def test_delete_vehicle(client: AsyncClient, auth_headers: dict, created_vehicle: dict):
    """Test the delete vehicle endpoint"""
    vehicle_id = created_vehicle["id"]
    response = await client.delete(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert response.status_code == 404


async def test_cannot_access_other_users_vehicle(
    client: AsyncClient, created_vehicle: dict, other_user_headers: dict
):
    """Test that a user cannot access another user's vehicle"""
    vehicle_id = created_vehicle["id"]
    response = await client.get(f"/vehicles/{vehicle_id}", headers=other_user_headers)
    assert response.status_code == 404


async def test_cannot_update_other_users_vehicle(
    client: AsyncClient, created_vehicle: dict, other_user_headers: dict
):
    """Test that a user cannot update another user's vehicle"""
    vehicle_id = created_vehicle["id"]
    response = await client.patch(
        f"/vehicles/{vehicle_id}",
        json={"baseline_odometer": 9999},
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_cannot_delete_other_users_vehicle(
    client: AsyncClient, created_vehicle: dict, other_user_headers: dict
):
    """Test that a user cannot delete another user's vehicle"""
    vehicle_id = created_vehicle["id"]
    response = await client.delete(f"/vehicles/{vehicle_id}", headers=other_user_headers)
    assert response.status_code == 404
