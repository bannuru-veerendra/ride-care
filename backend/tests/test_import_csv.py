"""Tests for fuel / service CSV import endpoints."""

from datetime import date, timedelta
from io import BytesIO

from httpx import AsyncClient


def _fuel_csv(rows: list[str]) -> bytes:
    header = (
        "date,odometer_km,liters,price_per_liter,total_cost,"
        "mileage_km_per_l,notes\n"
    )
    return (header + "\n".join(rows) + "\n").encode("utf-8")


def _service_csv(rows: list[str]) -> bytes:
    header = (
        "date,odometer_km,service_center,total_cost,services_done,"
        "next_service_date,next_service_odometer_km,notes\n"
    )
    return (header + "\n".join(rows) + "\n").encode("utf-8")


async def test_import_fuel_logs_csv(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    baseline = created_vehicle["current_odometer"]
    day = date.today() - timedelta(days=2)
    csv_bytes = _fuel_csv(
        [
            f"{day},{baseline + 100},,100,500,,first",
            f"{day + timedelta(days=1)},{baseline + 220},,100,400,,second",
        ]
    )

    response = await client.post(
        "/fuel_logs/import",
        params={"vehicle_id": vehicle_id},
        files={"file": ("fuel.csv", BytesIO(csv_bytes), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["imported"] == 2

    listed = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id, "size": 20},
        headers=auth_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    mileages = [item["mileage"] for item in listed.json()["items"]]
    assert all(m is not None for m in mileages)


async def test_import_fuel_logs_rejects_bad_rows(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    baseline = created_vehicle["current_odometer"]
    csv_bytes = _fuel_csv(
        [
            f"{date.today()},{baseline + 50},,100,0,,bad-cost",
        ]
    )
    response = await client.post(
        "/fuel_logs/import",
        params={"vehicle_id": vehicle_id},
        files={"file": ("fuel.csv", BytesIO(csv_bytes), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["message"] == "CSV import failed"
    assert detail["errors"]

    listed = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id, "size": 20},
        headers=auth_headers,
    )
    assert listed.json()["total"] == 0


async def test_import_fuel_logs_rejects_odometer_timeline(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    baseline = created_vehicle["current_odometer"]
    csv_bytes = _fuel_csv(
        [
            f"{date.today()},{baseline},,100,500,,not-above-baseline",
        ]
    )
    response = await client.post(
        "/fuel_logs/import",
        params={"vehicle_id": vehicle_id},
        files={"file": ("fuel.csv", BytesIO(csv_bytes), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["message"] == "CSV import failed"
    assert detail["errors"]
    assert detail["errors"][0]["row"] == 2
    assert "odometer" in detail["errors"][0]["message"].lower()

    listed = await client.get(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id, "size": 20},
        headers=auth_headers,
    )
    assert listed.json()["total"] == 0


async def test_import_fuel_rejects_oversized_file(
    client: AsyncClient,
    auth_headers: dict,
    created_vehicle: dict,
    monkeypatch,
):
    monkeypatch.setattr("app.utils.import_csv.MAX_IMPORT_BYTES", 80)
    vehicle_id = created_vehicle["id"]
    # Force chunked reader path to hit the capped max
    big = b"x" * 200
    response = await client.post(
        "/fuel_logs/import",
        params={"vehicle_id": vehicle_id},
        files={"file": ("fuel.csv", BytesIO(big), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["message"] == "CSV import failed"
    assert "too large" in detail["errors"][0]["message"].lower()


async def test_import_service_logs_csv(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    vehicle_id = created_vehicle["id"]
    baseline = created_vehicle["current_odometer"]
    csv_bytes = _service_csv(
        [
            (
                f"{date.today()},{baseline + 50},Local garage,1200,"
                f"oil_change; chain_lube,,,first service"
            ),
        ]
    )
    response = await client.post(
        "/service_logs/import",
        params={"vehicle_id": vehicle_id},
        files={"file": ("service.csv", BytesIO(csv_bytes), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["imported"] == 1

    listed = await client.get(
        "/service_logs/",
        params={"vehicle_id": vehicle_id, "size": 20},
        headers=auth_headers,
    )
    item = listed.json()["items"][0]
    assert item["services_done"] == ["oil_change", "chain_lube"]
    assert item["service_center"] == "Local garage"


async def test_import_service_logs_forbidden_other_user(
    client: AsyncClient,
    other_user_headers: dict,
    created_vehicle: dict,
):
    csv_bytes = _service_csv(
        [f"{date.today()},10500,Shop,500,oil_change,,"]
    )
    response = await client.post(
        "/service_logs/import",
        params={"vehicle_id": created_vehicle["id"]},
        files={"file": ("service.csv", BytesIO(csv_bytes), "text/csv")},
        headers=other_user_headers,
    )
    assert response.status_code == 404


async def test_import_fuel_round_trip_export(
    client: AsyncClient, auth_headers: dict, created_vehicle: dict
):
    """Export format can be re-imported onto another empty vehicle belonging to user."""
    vehicle_id = created_vehicle["id"]
    baseline = created_vehicle["current_odometer"]
    await client.post(
        "/fuel_logs/",
        params={"vehicle_id": vehicle_id},
        json={
            "date": str(date.today() - timedelta(days=1)),
            "odometer": baseline + 100,
            "total_cost": 500,
            "price_per_liter": 100,
            "notes": "seed",
        },
        headers=auth_headers,
    )
    exported = await client.get(
        "/fuel_logs/export",
        params={"vehicle_id": vehicle_id},
        headers=auth_headers,
    )
    assert exported.status_code == 200

    created = await client.post(
        "/vehicles/",
        json={
            "brand": "Honda",
            "vehicle_name": "Import Bike",
            "year": 2020,
            "baseline_odometer": baseline,
            "registration_number": "IMPORT99901",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    other_id = created.json()["id"]

    response = await client.post(
        "/fuel_logs/import",
        params={"vehicle_id": other_id},
        files={
            "file": (
                "fuel.csv",
                BytesIO(exported.content),
                "text/csv",
            )
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["imported"] == 1
