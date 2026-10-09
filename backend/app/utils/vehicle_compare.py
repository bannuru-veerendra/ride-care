"""Garage-wide compare aggregation."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCompareItem, VehicleCompareResponse
from app.utils.analytics import cost_per_km, km_driven, round_money
from app.utils.odometer import get_live_odometers_map
from app.utils.vehicle_summary import round_mileage


async def build_compare_response(
    db: AsyncSession,
    vehicles: list[Vehicle],
) -> VehicleCompareResponse:
    """Side-by-side cost and mileage for the given bikes."""
    live_odometers = await get_live_odometers_map(db, vehicles)
    vehicle_ids = [vehicle.id for vehicle in vehicles]

    fuel_result = await db.execute(
        select(
            FuelLog.vehicle_id,
            func.count().label("fill_ups"),
            func.coalesce(func.sum(FuelLog.total_cost), 0.0).label("fuel_spend"),
            func.avg(FuelLog.mileage).label("avg_mileage"),
        )
        .where(FuelLog.vehicle_id.in_(vehicle_ids))
        .group_by(FuelLog.vehicle_id)
    )
    fuel_by_vehicle = {row.vehicle_id: row for row in fuel_result.all()}

    service_result = await db.execute(
        select(
            ServiceLog.vehicle_id,
            func.count().label("service_count"),
            func.coalesce(func.sum(ServiceLog.total_cost), 0.0).label(
                "service_spend"
            ),
        )
        .where(ServiceLog.vehicle_id.in_(vehicle_ids))
        .group_by(ServiceLog.vehicle_id)
    )
    service_by_vehicle = {row.vehicle_id: row for row in service_result.all()}

    items: list[VehicleCompareItem] = []
    for vehicle in vehicles:
        fuel_row = fuel_by_vehicle.get(vehicle.id)
        service_row = service_by_vehicle.get(vehicle.id)
        fuel_spend = round_money(fuel_row.fuel_spend) if fuel_row else 0.0
        service_spend = (
            round_money(service_row.service_spend) if service_row else 0.0
        )
        combined = round_money(fuel_spend + service_spend)
        kilometers = km_driven(
            vehicle.current_odometer, live_odometers[vehicle.id]
        )
        items.append(
            VehicleCompareItem(
                vehicle_id=vehicle.id,
                brand=vehicle.brand,
                vehicle_name=vehicle.vehicle_name,
                year=vehicle.year,
                current_odometer=live_odometers[vehicle.id],
                km_driven=kilometers,
                avg_mileage=round_mileage(
                    fuel_row.avg_mileage if fuel_row else None
                ),
                fuel_spend=fuel_spend,
                service_spend=service_spend,
                combined_spend=combined,
                cost_per_km=cost_per_km(combined, kilometers),
                fill_up_count=int(fuel_row.fill_ups) if fuel_row else 0,
                service_count=(
                    int(service_row.service_count) if service_row else 0
                ),
            )
        )

    return VehicleCompareResponse(items=items)
