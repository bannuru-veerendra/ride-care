"""Chart analytics aggregation for one vehicle."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.vehicle import Vehicle
from app.schemas.vehicle import (
    MileageTrendPoint,
    MonthlySpendPoint,
    VehicleAnalyticsResponse,
)
from app.utils.analytics import cost_per_km, km_driven, round_money
from app.utils.dates import app_today
from app.utils.months import month_bounds, shift_month
from app.utils.odometer import get_live_odometer
from app.utils.vehicle_summary import round_mileage


async def build_analytics_response(
    db: AsyncSession,
    db_vehicle: Vehicle,
) -> VehicleAnalyticsResponse:
    """Chart-ready analytics scanned across fuel and service logs."""
    vehicle_id = db_vehicle.id
    totals_result = await db.execute(
        select(
            func.count().label("total_fill_ups"),
            func.coalesce(func.sum(FuelLog.total_cost), 0.0).label("total_spend"),
            func.coalesce(func.sum(FuelLog.liters), 0.0).label("total_liters"),
        ).where(FuelLog.vehicle_id == vehicle_id)
    )
    totals = totals_result.one()

    mileage_stats_result = await db.execute(
        select(
            func.avg(FuelLog.mileage),
            func.max(FuelLog.mileage),
            func.min(FuelLog.mileage),
        ).where(
            FuelLog.vehicle_id == vehicle_id,
            FuelLog.mileage.isnot(None),
        )
    )
    avg_raw, best_raw, worst_raw = mileage_stats_result.one()

    trend_result = await db.execute(
        select(FuelLog)
        .where(
            FuelLog.vehicle_id == vehicle_id,
            FuelLog.mileage.isnot(None),
        )
        .order_by(FuelLog.date.desc(), FuelLog.odometer.desc())
        .limit(10)
    )
    trend_logs = list(reversed(list(trend_result.scalars().all())))
    mileage_trend = [
        MileageTrendPoint(
            date=log.date,
            date_label=log.date.strftime("%d %b"),
            mileage=round_mileage(log.mileage) or 0.0,
            odometer=log.odometer,
        )
        for log in trend_logs
    ]

    today = app_today()
    monthly_spend: list[MonthlySpendPoint] = []
    for i in range(5, -1, -1):
        month_ref = shift_month(today, -i)
        start, end = month_bounds(month_ref)
        month_result = await db.execute(
            select(
                func.coalesce(func.sum(FuelLog.total_cost), 0.0),
                func.coalesce(func.sum(FuelLog.liters), 0.0),
            ).where(
                FuelLog.vehicle_id == vehicle_id,
                FuelLog.date >= start,
                FuelLog.date <= end,
            )
        )
        spend, liters = month_result.one()
        monthly_spend.append(
            MonthlySpendPoint(
                month=month_ref.strftime("%b"),
                year_month=month_ref.strftime("%Y-%m"),
                spend=float(spend),
                liters=round(float(liters), 2),
            )
        )

    service_totals_result = await db.execute(
        select(
            func.count().label("service_count"),
            func.coalesce(func.sum(ServiceLog.total_cost), 0.0).label(
                "service_spend"
            ),
        ).where(ServiceLog.vehicle_id == vehicle_id)
    )
    service_totals = service_totals_result.one()
    fuel_spend = round_money(totals.total_spend)
    service_spend = round_money(service_totals.service_spend)
    combined_spend = round_money(fuel_spend + service_spend)
    live_odometer = await get_live_odometer(db, db_vehicle)
    kilometers = km_driven(db_vehicle.current_odometer, live_odometer)

    return VehicleAnalyticsResponse(
        vehicle_id=vehicle_id,
        total_spend=fuel_spend,
        total_liters=round(float(totals.total_liters), 2),
        avg_mileage=round_mileage(avg_raw),
        best_mileage=round_mileage(best_raw),
        worst_mileage=round_mileage(worst_raw),
        total_fill_ups=int(totals.total_fill_ups),
        mileage_trend=mileage_trend,
        monthly_spend=monthly_spend,
        service_spend=service_spend,
        service_count=int(service_totals.service_count),
        combined_spend=combined_spend,
        km_driven=kilometers,
        cost_per_km=cost_per_km(combined_spend, kilometers),
        fuel_cost_per_km=cost_per_km(fuel_spend, kilometers),
        service_cost_per_km=cost_per_km(service_spend, kilometers),
    )
