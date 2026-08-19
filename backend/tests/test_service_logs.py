from datetime import date, timedelta
from httpx import AsyncClient

from app.utils.dates import app_today


async def test_create_service_log_success(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test creating a service log successfully"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "service_center": "Bharat Automobiles",
            "total_cost": 1500,
            "services_done": ["Engine oil", "Chain lube"],
            "next_service_date": str(date.today() + timedelta(days=90)),
            "next_service_odometer": 15000,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["services_done"] == ["Engine oil", "Chain lube"]
    assert data["next_service_odometer"] == 15000
    assert "id" in data


async def test_create_service_log_empty_services(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test creating a service log with empty services returns 422"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": [],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_create_service_log_rejects_future_date(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test creating a service log with a future date returns 422"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(app_today() + timedelta(days=1)),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_create_service_log_invalid_next_odometer(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test creating a service log with invalid next odometer returns 422"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
            "next_service_odometer": 11000,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_create_service_log_rejects_odometer_below_baseline(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Service odometer below baseline would inflate live odometer incorrectly — reject it."""
    vehicle_id = created_vehicle["id"]
    baseline = created_vehicle["baseline_odometer"]
    response = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": baseline - 1,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "baseline" in response.json()["detail"].lower()


async def test_update_service_log_rejects_next_odometer_below_existing(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Partial PATCH cannot set next_service_odometer below the existing odometer."""
    vehicle_id = created_vehicle["id"]
    create_resp = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
            "next_service_odometer": 15000,
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    log_id = create_resp.json()["id"]

    response = await client.patch(
        f"/service_logs/{log_id}",
        params={"vehicle_id": vehicle_id},
        json={"next_service_odometer": 11000},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "next service odometer" in response.json()["detail"].lower()


async def test_create_service_log_negative_total_cost(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test creating a service log with negative total_cost returns 422"""
    vehicle_id = created_vehicle["id"]
    response = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": -100,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_get_service_logs(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test getting service logs successfully"""
    vehicle_id = created_vehicle["id"]
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
    response = await client.get(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "has_more" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 1
    assert data["total"] == 1


async def test_get_service_logs_ordered_by_date_desc(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Service logs are listed newest date first, even if entered out of order."""
    vehicle_id = created_vehicle["id"]
    later_date = str(date.today())
    earlier_date = str(date.today() - timedelta(days=30))

    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": later_date,
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Chain lube"],
        },
        headers=auth_headers,
    )
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": earlier_date,
            "odometer": 11000,
            "total_cost": 1200,
            "services_done": ["Oil change"],
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert data["items"][0]["date"] == later_date
    assert data["items"][0]["odometer"] == 12000
    assert data["items"][1]["date"] == earlier_date
    assert data["items"][1]["odometer"] == 11000


async def test_get_next_service(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test getting the next service log successfully"""
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
            "next_service_odometer": 15000,
        },
        headers=auth_headers,
    )
    response = await client.get(
        "/service_logs/next",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["next_service_date"] == next_date


async def test_get_next_service_uses_most_recent_visit(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Next service comes from the latest visit, not an older overdue next date."""
    vehicle_id = created_vehicle["id"]
    older_next = str(date.today() - timedelta(days=30))
    newer_next = str(date.today() + timedelta(days=90))

    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today() - timedelta(days=180)),
            "odometer": 11000,
            "total_cost": 1200,
            "services_done": ["Oil change"],
            "next_service_date": older_next,
            "next_service_odometer": 14000,
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
            "services_done": ["Chain lube"],
            "next_service_date": newer_next,
            "next_service_odometer": 15000,
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/service_logs/next",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["next_service_date"] == newer_next


async def test_get_next_service_none(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test getting the next service log when there is no next service returns None"""
    vehicle_id = created_vehicle["id"]
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
    response = await client.get(
        "/service_logs/next",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() is None


async def test_get_next_service_cleared_after_due_visit(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """A later visit on the due date clears the previous next-service schedule."""
    vehicle_id = created_vehicle["id"]
    due_date = str(date.today())

    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today() - timedelta(days=90)),
            "odometer": 11000,
            "total_cost": 1500,
            "services_done": ["Oil change"],
            "next_service_date": due_date,
        },
        headers=auth_headers,
    )
    await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": due_date,
            "odometer": 12000,
            "total_cost": 1800,
            "services_done": ["Oil change"],
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/service_logs/next",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() is None


async def test_update_service_log(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test updating a service log successfully"""
    vehicle_id = created_vehicle["id"]
    create_resp = await client.post(
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
    log_id = create_resp.json()["id"]

    response = await client.patch(
        f"/service_logs/{log_id}",
        params={"vehicle_id": vehicle_id},
        json={"services_done": ["Engine oil", "Brake pads"], "total_cost": 2500},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["services_done"] == ["Engine oil", "Brake pads"]
    assert data["total_cost"] == 2500


async def test_update_service_log_clears_next_service_fields(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Explicit null on PATCH clears next service date and odometer."""
    vehicle_id = created_vehicle["id"]
    create_resp = await client.post(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
            "next_service_date": str(date.today() + timedelta(days=90)),
            "next_service_odometer": 15000,
        },
        headers=auth_headers,
    )
    log_id = create_resp.json()["id"]

    response = await client.patch(
        f"/service_logs/{log_id}",
        params={"vehicle_id": vehicle_id},
        json={"next_service_date": None, "next_service_odometer": None},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["next_service_date"] is None
    assert data["next_service_odometer"] is None


async def test_delete_service_log(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Test deleting a service log successfully"""
    vehicle_id = created_vehicle["id"]
    create_resp = await client.post(
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
    log_id = create_resp.json()["id"]

    response = await client.delete(
        f"/service_logs/{log_id}",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 204

    response = await client.get(
        f"/service_logs/{log_id}",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_cannot_access_other_users_service_logs(
    client: AsyncClient, created_vehicle: dict, other_user_headers: dict
):
    """Test that a user cannot access another user's service logs"""
    vehicle_id = created_vehicle["id"]
    response = await client.get(
        "/service_logs/",
        params={"vehicle_id": vehicle_id},
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_service_log_wrong_vehicle(
    client: AsyncClient, auth_headers: dict
):
    """Test creating a service log for a non-existent vehicle returns 404"""
    fake_vehicle_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        "/service_logs/",
        params={"vehicle_id": fake_vehicle_id},
        json={
            "date": str(date.today()),
            "odometer": 12000,
            "total_cost": 1500,
            "services_done": ["Engine oil"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 404