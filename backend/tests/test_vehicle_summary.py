from calendar import monthrange
from datetime import date, timedelta

from httpx import AsyncClient

from app.utils.dates import app_today


def _shift_month(ref: date, months: int) -> date:
    year = ref.year + (ref.month - 1 + months) // 12
    month = (ref.month - 1 + months) % 12 + 1
    return date(year, month, 1)


async def test_vehicle_summary_empty(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Summary returns zeroed aggregations when the vehicle has no logs."""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == vehicle_id
    assert data["fuel_log_count"] == 0
    assert data["average_mileage"] is None
    assert data["this_month_spend"] == 0
    assert data["last_month_spend"] == 0
    assert data["this_month_mileage"] is None
    assert data["last_month_mileage"] is None
    assert data["recent_filled_month_mileage"] is None
    assert data["prior_filled_month_mileage"] is None
    assert data["recent_filled_month_label"] is None
    assert data["prior_filled_month_label"] is None
    assert data["recent_fuel_logs"] == []
    assert data["next_service"] is None


async def test_vehicle_summary_mileage_trend_skips_empty_current_month(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Mileage trend uses the last two months that have fill-ups, not calendar months."""
    vehicle_id = created_vehicle["id"]
    today = app_today()
    last_month = _shift_month(today, -1)
    two_months_ago = _shift_month(today, -2)

    last_month_day = min(12, monthrange(last_month.year, last_month.month)[1])
    prior_day = min(12, monthrange(two_months_ago.year, two_months_ago.month)[1])

    # First fill establishes mileage baseline chain
    first = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date(two_months_ago.year, two_months_ago.month, prior_day)),
            "odometer": 10500,
            "total_cost": 400,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert first.status_code == 201

    second = await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date(last_month.year, last_month.month, last_month_day)),
            "odometer": 11000,
            "total_cost": 500,
            "price_per_liter": 100,
        },
        headers=auth_headers,
    )
    assert second.status_code == 201

    response = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Current calendar month has no logs
    assert data["this_month_spend"] == 0
    assert data["this_month_mileage"] is None
    # Trend still compares the two filled months
    assert data["recent_filled_month_mileage"] is not None
    assert data["prior_filled_month_mileage"] is not None
    assert data["recent_filled_month_label"] == last_month.strftime("%b")
    assert data["prior_filled_month_label"] == two_months_ago.strftime("%b")


async def test_vehicle_summary_aggregates_across_all_logs(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Spend and mileage averages scan every log, not just a page."""
    vehicle_id = created_vehicle["id"]
    today = app_today()
    # Stay on/before today — using a fixed day like 15 fails early in the month
    this_month_date = today
    earlier_this_month = date(today.year, today.month, max(1, today.day - 2))
    last_month_ref = _shift_month(today, -1)
    last_month_day = min(10, monthrange(last_month_ref.year, last_month_ref.month)[1])
    last_month_date = date(last_month_ref.year, last_month_ref.month, last_month_day)

    # Older fill-up last month (mileage computed from baseline 10000)
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
    # Two fill-ups this month
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

    next_date = str(today + timedelta(days=45))
    service_resp = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(today),
            "odometer": 11700,
            "total_cost": 1500,
            "services_done": ["Oil change"],
            "next_service_date": next_date,
            "next_service_odometer": 14000,
        },
        headers=auth_headers,
    )
    assert service_resp.status_code == 201

    response = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["fuel_log_count"] == 3
    assert data["this_month_spend"] == 1100
    assert data["last_month_spend"] == 400
    assert data["average_mileage"] is not None
    assert data["this_month_mileage"] is not None
    assert data["last_month_mileage"] is not None
    assert data["recent_filled_month_mileage"] is not None
    assert data["prior_filled_month_mileage"] is not None
    assert data["recent_filled_month_label"] is not None
    assert data["prior_filled_month_label"] is not None
    assert len(data["recent_fuel_logs"]) == 3
    assert data["recent_fuel_logs"][0]["odometer"] == 11600
    assert data["next_service"] is not None
    assert data["next_service"]["next_service_date"] == next_date


async def test_vehicle_summary_recent_logs_capped_at_three(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Recent fill-ups return at most the three newest logs."""
    vehicle_id = created_vehicle["id"]
    today = app_today()
    odometer = 10100
    for offset in range(4):
        await client.post(
            "/fuel_logs/",
            params={"vehicle_id": vehicle_id},
            json={
                "date": str(today - timedelta(days=30 - offset)),
                "odometer": odometer,
                "total_cost": 500,
                "price_per_liter": 100,
            },
            headers=auth_headers,
        )
        odometer += 400

    response = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fuel_log_count"] == 4
    assert len(data["recent_fuel_logs"]) == 3
    assert data["recent_fuel_logs"][0]["odometer"] == 11300


async def test_vehicle_summary_forbidden_for_other_user(
    client: AsyncClient,
    other_user_headers: dict,
    created_vehicle: dict,
):
    """Other users cannot read a vehicle summary they do not own."""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        f"/vehicles/{vehicle_id}/summary",
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_vehicle_summary_unauthenticated(
    client: AsyncClient, created_vehicle: dict
):
    """Summary requires authentication."""
    vehicle_id = created_vehicle["id"]
    response = await client.get(f"/vehicles/{vehicle_id}/summary")
    assert response.status_code == 401
