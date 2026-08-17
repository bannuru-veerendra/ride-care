from calendar import monthrange
from datetime import date, timedelta

from httpx import AsyncClient

from app.utils.dates import app_today


def _shift_month(ref: date, months: int) -> date:
    year = ref.year + (ref.month - 1 + months) // 12
    month = (ref.month - 1 + months) % 12 + 1
    return date(year, month, 1)


async def test_vehicle_analytics_empty(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Analytics returns zeroed totals and empty trend when there are no logs."""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == vehicle_id
    assert data["total_spend"] == 0
    assert data["total_liters"] == 0
    assert data["avg_mileage"] is None
    assert data["best_mileage"] is None
    assert data["worst_mileage"] is None
    assert data["total_fill_ups"] == 0
    assert data["mileage_trend"] == []
    assert len(data["monthly_spend"]) == 6
    assert all(point["spend"] == 0 for point in data["monthly_spend"])
    assert data["service_spend"] == 0
    assert data["service_count"] == 0
    assert data["combined_spend"] == 0
    assert data["km_driven"] == 0
    assert data["cost_per_km"] is None
    assert data["fuel_cost_per_km"] is None
    assert data["service_cost_per_km"] is None


async def test_vehicle_analytics_aggregates(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Analytics scans all fuel logs for summary, trend, and monthly spend."""
    vehicle_id = created_vehicle["id"]
    today = app_today()
    this_month_date = today
    earlier_this_month = date(today.year, today.month, max(1, today.day - 2))
    last_month_ref = _shift_month(today, -1)
    last_month_day = min(10, monthrange(last_month_ref.year, last_month_ref.month)[1])
    last_month_date = date(last_month_ref.year, last_month_ref.month, last_month_day)

    last_month_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(last_month_date),
            "odometer": 10500,
            "total_cost": 400,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert last_month_resp.status_code == 201

    earlier_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(earlier_this_month),
            "odometer": 11000,
            "total_cost": 500,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert earlier_resp.status_code == 201

    this_month_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(this_month_date),
            "odometer": 11600,
            "total_cost": 600,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert this_month_resp.status_code == 201

    response = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total_fill_ups"] == 3
    assert data["total_spend"] == 1500
    assert data["total_liters"] == 15.0
    assert data["avg_mileage"] is not None
    assert data["best_mileage"] is not None
    assert data["worst_mileage"] is not None
    assert data["best_mileage"] >= data["worst_mileage"]

    assert len(data["mileage_trend"]) == 3
    odometers = [point["odometer"] for point in data["mileage_trend"]]
    assert odometers == sorted(odometers)
    assert data["mileage_trend"][-1]["odometer"] == 11600

    assert len(data["monthly_spend"]) == 6
    current_bucket = data["monthly_spend"][-1]
    assert current_bucket["year_month"] == today.strftime("%Y-%m")
    assert current_bucket["spend"] == 1100
    last_bucket = data["monthly_spend"][-2]
    assert last_bucket["year_month"] == last_month_ref.strftime("%Y-%m")
    assert last_bucket["spend"] == 400


async def test_vehicle_analytics_trend_capped_at_ten(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Mileage trend returns at most the 10 newest logs with mileage."""
    vehicle_id = created_vehicle["id"]
    today = app_today()
    odometer = 10100
    for offset in range(12):
        resp = await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": str(today - timedelta(days=40 - offset)),
                "odometer": odometer,
                "total_cost": 500,
                "price_per_liter": 100,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        odometer += 400

    response = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_fill_ups"] == 12
    assert len(data["mileage_trend"]) == 10
    odometers = [point["odometer"] for point in data["mileage_trend"]]
    assert odometers == sorted(odometers)


async def test_vehicle_analytics_forbidden_for_other_user(
    client: AsyncClient,
    other_user_headers: dict,
    created_vehicle: dict,
):
    """Other users cannot read analytics for a vehicle they do not own."""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_vehicle_analytics_unauthenticated(
    client: AsyncClient, created_vehicle: dict
):
    """Analytics requires authentication."""
    vehicle_id = created_vehicle["id"]
    response = await client.get(f"/vehicles/{vehicle_id}/analytics")
    assert response.status_code == 401


async def test_vehicle_analytics_cost_per_km_includes_service(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """cost_per_km uses fuel + service spend over km since baseline."""
    vehicle_id = created_vehicle["id"]
    today = app_today()

    fuel_resp = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
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
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today),
            "odometer": 10500,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert service_resp.status_code == 201

    response = await client.get(
        f"/vehicles/{vehicle_id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_spend"] == 500
    assert data["service_spend"] == 1500
    assert data["service_count"] == 1
    assert data["combined_spend"] == 2000
    assert data["km_driven"] == 500
    assert data["cost_per_km"] == 4.0
    assert data["fuel_cost_per_km"] == 1.0
    assert data["service_cost_per_km"] == 3.0

