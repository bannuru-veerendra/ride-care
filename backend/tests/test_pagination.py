from datetime import date, timedelta

from httpx import AsyncClient


async def test_fuel_logs_default_page_size(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test fuel logs default page returns all items when under the limit"""
    vehicle_id = created_vehicle["id"]

    # Create oldest → newest so odometer timeline stays valid
    for i in range(5):
        await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": str(date.today() - timedelta(days=4 - i)),
                "odometer": 10100 + (i * 100),
                "total_cost": 500,
                "price_per_liter": 100,
            },
            headers=auth_headers,
        )

    response = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == 5
    assert data["has_more"] is False
    assert data["next_cursor"] is None


async def test_fuel_logs_cursor_pagination(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test fuel logs cursor pagination returns non-overlapping pages"""
    vehicle_id = created_vehicle["id"]

    for i in range(5):
        await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": str(date.today() - timedelta(days=4 - i)),
                "odometer": 10100 + (i * 100),
                "total_cost": 500,
                "price_per_liter": 100,
            },
            headers=auth_headers,
        )

    page1 = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id, "size": 3},
        headers=auth_headers,
    )
    data1 = page1.json()
    assert len(data1["items"]) == 3
    assert data1["has_more"] is True
    assert data1["next_cursor"] is not None
    assert data1["total"] == 5

    page2 = await client.get(
        "/fuel_logs/",
        params={
            "vehicle_id": vehicle_id,
            "size": 3,
            "cursor": data1["next_cursor"],
        },
        headers=auth_headers,
    )
    data2 = page2.json()
    assert len(data2["items"]) == 2
    assert data2["has_more"] is False
    assert data2["next_cursor"] is None

    page1_ids = {item["id"] for item in data1["items"]}
    page2_ids = {item["id"] for item in data2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


async def test_vehicles_pagination(client: AsyncClient, auth_headers: dict):
    """Test vehicles endpoint returns a paginated response"""
    for i in range(3):
        await client.post(
            "/vehicles/",
            json={
                "brand": f"Brand{i}",
                "vehicle_name": f"Vehicle{i}",
                "year": 2020,
                "registration_number": f"KA0{i}AB000{i}",
                "baseline_odometer": 0,
            },
            headers=auth_headers,
        )

    response = await client.get("/vehicles/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["has_more"] is False


async def test_page_size_limit(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test page size above 100 returns 422"""
    response = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": created_vehicle["id"], "size": 101},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_newest_first_ordering(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test fuel logs are returned newest first"""
    vehicle_id = created_vehicle["id"]

    dates = ["2025-01-01", "2025-03-01", "2025-06-01"]
    for i, log_date in enumerate(dates):
        await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": log_date,
                "odometer": 10100 + (i * 500),
                "total_cost": 500,
                "price_per_liter": 100,
            },
            headers=auth_headers,
        )

    response = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    items = response.json()["items"]
    returned_dates = [item["date"] for item in items]

    assert returned_dates == sorted(returned_dates, reverse=True)
