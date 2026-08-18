from httpx import AsyncClient


async def test_vehicle_list_cached(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """
    Second request for vehicle list hits cache.
    Both responses return the same data.
    """
    response1 = await client.get("/vehicles/", headers=auth_headers)
    response2 = await client.get("/vehicles/", headers=auth_headers)

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()


async def test_vehicle_cache_invalidated_on_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """
    Creating a vehicle invalidates the list cache.
    New vehicle appears in the next list response.
    """
    # Warm the cache
    response1 = await client.get("/vehicles/", headers=auth_headers)
    initial_count = response1.json()["total"]

    # Create a new vehicle
    await client.post(
        "/vehicles/",
        json={
            "brand": "Honda",
            "vehicle_name": "Shine",
            "year": 2022,
            "registration_number": "KA02XY5678",
            "current_odometer": 0,
        },
        headers=auth_headers,
    )

    # Cache should be invalidated — new vehicle should appear
    response2 = await client.get("/vehicles/", headers=auth_headers)
    assert response2.json()["total"] == initial_count + 1


async def test_vehicle_detail_cached(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Single vehicle detail is cached."""
    vehicle_id = created_vehicle["id"]

    response1 = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    response2 = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)

    assert response1.status_code == 200
    assert response1.json() == response2.json()


async def test_vehicle_cache_invalidated_on_update(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """
    Updating a vehicle invalidates its detail cache.
    Updated value appears in the next response.
    """
    vehicle_id = created_vehicle["id"]

    # Warm the cache
    await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)

    # Update odometer
    await client.patch(
        f"/vehicles/{vehicle_id}",
        json={"current_odometer": 99999},
        headers=auth_headers,
    )

    # Should reflect updated value
    response = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert response.json()["current_odometer"] == 99999


async def test_vehicle_cache_invalidated_on_delete(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """
    Deleting a vehicle invalidates list cache.
    Deleted vehicle does not appear in next list response.
    """
    vehicle_id = created_vehicle["id"]

    # Warm the cache
    response1 = await client.get("/vehicles/", headers=auth_headers)
    initial_count = response1.json()["total"]

    # Delete vehicle
    await client.delete(f"/vehicles/{vehicle_id}", headers=auth_headers)

    # List should not contain deleted vehicle
    response2 = await client.get("/vehicles/", headers=auth_headers)
    assert response2.json()["total"] == initial_count - 1
    ids = [v["id"] for v in response2.json()["items"]]
    assert vehicle_id not in ids


async def test_next_service_consistent(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Next service endpoint returns stable results."""
    vehicle_id = created_vehicle["id"]

    response1 = await client.get(
        "/service_logs/next",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    response2 = await client.get(
        "/service_logs/next",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )

    assert response1.status_code == 200
    assert response1.json() == response2.json()


async def test_next_service_updates_after_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Creating a service log with next_service_date updates the next endpoint."""
    from datetime import date, timedelta

    vehicle_id = created_vehicle["id"]

    next_date = str(date.today() + timedelta(days=90))
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
            "next_service_date": next_date,
        },
        headers=auth_headers,
    )

    response2 = await client.get(
        "/service_logs/next",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response2.json() is not None
    assert response2.json()["next_service_date"] == next_date


async def test_vehicle_summary_cached(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Summary endpoint is cached across identical requests."""
    vehicle_id = created_vehicle["id"]

    response1 = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    response2 = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )

    assert response1.status_code == 200
    assert response1.json() == response2.json()


async def test_vehicle_analytics_cached(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Analytics endpoint is cached across identical requests."""
    vehicle_id = created_vehicle["id"]

    response1 = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    response2 = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )

    assert response1.status_code == 200
    assert response1.json() == response2.json()


async def test_vehicle_analytics_cache_invalidated_on_fuel_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Creating a fuel log invalidates analytics cache."""
    from app.utils.dates import app_today

    vehicle_id = created_vehicle["id"]

    warm = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert warm.json()["total_fill_ups"] == 0

    create_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            "odometer": 10500,
            "total_cost": 500,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    refreshed = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["total_fill_ups"] == 1
    assert refreshed.json()["total_spend"] == 500


async def test_vehicle_analytics_cache_invalidated_on_service_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Creating a service log invalidates analytics cache (cost-per-km)."""
    from app.utils.dates import app_today

    vehicle_id = created_vehicle["id"]

    warm = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert warm.json()["service_spend"] == 0

    create_resp = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    refreshed = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["service_spend"] == 1500
    assert refreshed.json()["combined_spend"] == 1500
    assert refreshed.json()["km_driven"] == 2000
    assert refreshed.json()["cost_per_km"] == 0.75


async def test_vehicle_compare_cache_invalidated_on_fuel_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Creating a fuel log invalidates garage compare cache."""
    from app.utils.dates import app_today

    vehicle_id = created_vehicle["id"]

    warm = await client.get("/vehicles/compare", headers=auth_headers)
    item = next(v for v in warm.json()["items"] if v["vehicle_id"] == vehicle_id)
    assert item["fill_up_count"] == 0
    assert item["cost_per_km"] is None

    create_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            "odometer": 10500,
            "total_cost": 500,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    refreshed = await client.get("/vehicles/compare", headers=auth_headers)
    item = next(
        v for v in refreshed.json()["items"] if v["vehicle_id"] == vehicle_id
    )
    assert item["fill_up_count"] == 1
    assert item["fuel_spend"] == 500
    assert item["km_driven"] == 500
    assert item["cost_per_km"] == 1.0


async def test_vehicle_summary_cache_invalidated_on_fuel_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Creating a fuel log invalidates summary cache."""
    from app.utils.dates import app_today

    vehicle_id = created_vehicle["id"]

    warm = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert warm.json()["fuel_log_count"] == 0

    create_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            "odometer": 10500,
            "total_cost": 500,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    refreshed = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["fuel_log_count"] == 1


async def test_vehicle_detail_cache_invalidated_on_service_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Creating a service log invalidates vehicle detail live odometer cache."""
    from app.utils.dates import app_today

    vehicle_id = created_vehicle["id"]

    warm = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert warm.json()["current_odometer"] == created_vehicle["current_odometer"]

    create_resp = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            "odometer": 12500,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    refreshed = await client.get(f"/vehicles/{vehicle_id}", headers=auth_headers)
    assert refreshed.status_code == 200
    assert refreshed.json()["current_odometer"] == 12500


async def test_vehicle_list_cache_invalidated_on_fuel_create(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Creating a fuel log invalidates vehicle list live odometer cache."""
    from app.utils.dates import app_today

    vehicle_id = created_vehicle["id"]

    warm = await client.get("/vehicles/", headers=auth_headers)
    listed = next(v for v in warm.json()["items"] if v["id"] == vehicle_id)
    assert listed["current_odometer"] == created_vehicle["current_odometer"]

    create_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today()),
            "odometer": 10800,
            "total_cost": 500,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    refreshed = await client.get("/vehicles/", headers=auth_headers)
    listed = next(v for v in refreshed.json()["items"] if v["id"] == vehicle_id)
    assert listed["current_odometer"] == 10800
