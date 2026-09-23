"""RideCare Health — ranked signals + one recommended action (no fake score)."""

from __future__ import annotations

from datetime import date

from app.models.document import Document
from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.vehicle import Vehicle
from app.schemas.vehicle import (
    CostHealth,
    HealthEvidence,
    HealthSignal,
    MileageHealth,
    RecommendedAction,
    ServicePrediction,
    VehicleHealthResponse,
)
from app.utils.analytics import cost_per_km, km_driven, round_money
from app.utils.auto_due import suggest_next_due
from app.utils.numbers import round_2
from app.utils.reminders import (
    build_document_reminders,
    build_service_reminder,
    find_active_next_service,
)

# Mileage: need enough fill-ups; decline if recent half is clearly worse.
MILEAGE_MIN_SAMPLES = 6
MILEAGE_DECLINE_RATIO = 0.10  # 10% worse
MILEAGE_DECLINE_ABS = 1.0  # or at least 1 km/l drop

# Riding rate for catalog / schedule estimates.
RIDING_RATE_MIN_DAYS = 14
RIDING_RATE_MIN_POINTS = 3


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round_2(sum(values) / len(values))


def riding_rate_km_per_day(fuel_logs: list[FuelLog]) -> float | None:
    """km/day from oldest→newest fill-up odometer over the span."""
    points = sorted(
        ((log.date, float(log.odometer)) for log in fuel_logs),
        key=lambda item: (item[0], item[1]),
    )
    if len(points) < RIDING_RATE_MIN_POINTS:
        return None
    first_date, first_odo = points[0]
    last_date, last_odo = points[-1]
    days = (last_date - first_date).days
    if days < RIDING_RATE_MIN_DAYS:
        return None
    distance = last_odo - first_odo
    if distance <= 0:
        return None
    return round_2(distance / days)


def _cost_confidence(fill_ups: int, kilometers: float) -> str:
    if kilometers <= 0 or fill_ups < 3:
        return "insufficient"
    if fill_ups < 5:
        return "low"
    if fill_ups < 10:
        return "medium"
    return "high"


def _mileage_health(fuel_logs: list[FuelLog]) -> MileageHealth:
    mileages = [
        float(log.mileage)
        for log in sorted(
            (log for log in fuel_logs if log.mileage is not None),
            key=lambda log: (log.date, log.odometer),
        )
    ][-10:]
    n = len(mileages)
    if n < MILEAGE_MIN_SAMPLES:
        return MileageHealth(
            trend="insufficient",
            recent_avg=None,
            earlier_avg=None,
            delta=None,
            sample_n=n,
            detail=(
                f"Need at least {MILEAGE_MIN_SAMPLES} fill-ups with mileage "
                f"to judge a trend (have {n})."
            ),
        )

    mid = n // 2
    earlier = mileages[:mid]
    recent = mileages[mid:]
    earlier_avg = _avg(earlier)
    recent_avg = _avg(recent)
    assert earlier_avg is not None and recent_avg is not None
    delta = round_2(recent_avg - earlier_avg)

    if (
        delta <= -MILEAGE_DECLINE_ABS
        and recent_avg <= earlier_avg * (1 - MILEAGE_DECLINE_RATIO)
    ):
        trend = "down"
        detail = (
            f"Recent avg {recent_avg} km/l is down from {earlier_avg} km/l "
            f"across {n} fill-ups — check tyre pressure / air filter / riding style."
        )
    elif delta >= MILEAGE_DECLINE_ABS and recent_avg >= earlier_avg * (
        1 + MILEAGE_DECLINE_RATIO
    ):
        trend = "up"
        detail = (
            f"Recent avg {recent_avg} km/l is up from {earlier_avg} km/l "
            f"across {n} fill-ups."
        )
    else:
        trend = "flat"
        detail = (
            f"Mileage looks steady ({recent_avg} km/l recently vs "
            f"{earlier_avg} earlier across {n} fill-ups)."
        )

    return MileageHealth(
        trend=trend,
        recent_avg=recent_avg,
        earlier_avg=earlier_avg,
        delta=delta,
        sample_n=n,
        detail=detail,
    )


def _service_prediction(
    *,
    service_logs: list[ServiceLog],
    active_next_service: ServiceLog | None,
    live_odometer: float,
    today: date,
    riding_rate: float | None,
) -> ServicePrediction:
    if active_next_service is not None:
        next_date = active_next_service.next_service_date
        next_odo = active_next_service.next_service_odometer
        days_until = (next_date - today).days if next_date is not None else None
        km_until = (
            round_2(float(next_odo) - live_odometer)
            if next_odo is not None
            else None
        )
        detail_bits: list[str] = ["Using the next-due you set on a service visit."]
        if riding_rate is not None and km_until is not None and km_until > 0:
            days_by_km = int(round(km_until / riding_rate))
            detail_bits.append(
                f"At ~{riding_rate} km/day, the km target is roughly "
                f"{days_by_km} day{'s' if days_by_km != 1 else ''} away."
            )
        elif riding_rate is None and km_until is not None:
            detail_bits.append(
                "Not enough riding data to estimate when you will hit the km target."
            )
        return ServicePrediction(
            source="rider_schedule",
            predicted_date=next_date,
            predicted_odometer=(
                round_2(float(next_odo)) if next_odo is not None else None
            ),
            days_until=days_until,
            km_until=km_until,
            riding_rate_km_per_day=riding_rate,
            detail=" ".join(detail_bits),
            matched_task=None,
        )

    for log in service_logs:
        tags = list(log.services_done or [])
        if not tags:
            continue
        suggestion = suggest_next_due(
            services_done=tags,
            visit_date=log.date,
            visit_odometer=float(log.odometer),
        )
        if not suggestion.matched_tasks:
            continue
        if (
            suggestion.next_service_date is None
            and suggestion.next_service_odometer is None
        ):
            continue

        days_until = (
            (suggestion.next_service_date - today).days
            if suggestion.next_service_date is not None
            else None
        )
        km_until = (
            round_2(float(suggestion.next_service_odometer) - live_odometer)
            if suggestion.next_service_odometer is not None
            else None
        )
        task = suggestion.matched_tasks[0]
        detail = f"Estimated from last “{task}” using the maintenance catalog."
        if riding_rate is None:
            detail += (
                " Thin riding history — treat the date/km as a guide, not a forecast."
            )
        return ServicePrediction(
            source="catalog_estimate",
            predicted_date=suggestion.next_service_date,
            predicted_odometer=suggestion.next_service_odometer,
            days_until=days_until,
            km_until=km_until,
            riding_rate_km_per_day=riding_rate,
            detail=detail,
            matched_task=task,
        )

    return ServicePrediction(
        source="insufficient",
        predicted_date=None,
        predicted_odometer=None,
        days_until=None,
        km_until=None,
        riding_rate_km_per_day=riding_rate,
        detail=(
            "No next-service schedule yet. Log a service and set next due, "
            "or use “Fill from guide” on a tagged visit."
        ),
        matched_task=None,
    )


def build_vehicle_health(
    *,
    vehicle: Vehicle,
    fuel_logs: list[FuelLog],
    service_logs: list[ServiceLog],
    documents: list[Document],
    live_odometer: float,
    today: date,
) -> VehicleHealthResponse:
    """Compose ranked health signals from existing garage data."""
    muted = bool(vehicle.reminders_muted)
    next_service = find_active_next_service(service_logs)
    service_reminder = build_service_reminder(
        next_service,
        today=today,
        live_odometer=live_odometer,
    )
    document_reminders = (
        [] if muted else build_document_reminders(documents, today=today)
    )

    riding_rate = riding_rate_km_per_day(fuel_logs)
    prediction = _service_prediction(
        service_logs=service_logs,
        active_next_service=next_service,
        live_odometer=live_odometer,
        today=today,
        riding_rate=riding_rate,
    )
    mileage = _mileage_health(fuel_logs)

    fuel_spend = round_money(sum(float(log.total_cost) for log in fuel_logs))
    service_spend = round_money(
        sum(float(log.total_cost) for log in service_logs)
    )
    kilometers = km_driven(float(vehicle.current_odometer), live_odometer)
    combined = round_money(fuel_spend + service_spend)
    cpk = cost_per_km(combined, kilometers)
    fill_ups = len(fuel_logs)
    cost_conf = _cost_confidence(fill_ups, kilometers)
    if cpk is None:
        cost_detail = "Need odometer progress (km driven) to compute ₹/km."
    else:
        cost_detail = (
            f"₹{cpk}/km from {fill_ups} fill-up"
            f"{'' if fill_ups == 1 else 's'} over {kilometers} km "
            f"(fuel + service)."
        )
    cost = CostHealth(
        cost_per_km=cpk,
        km_driven=kilometers,
        fill_ups=fill_ups,
        confidence=cost_conf,  # type: ignore[arg-type]
        detail=cost_detail,
    )

    signals: list[HealthSignal] = []

    if not muted and service_reminder.status == "overdue":
        bits: list[str] = []
        if service_reminder.days_until is not None:
            bits.append(f"{abs(service_reminder.days_until)} day(s) past due")
        if service_reminder.km_until is not None:
            bits.append(f"{abs(service_reminder.km_until)} km past due")
        evidence: list[HealthEvidence] = []
        if service_reminder.next_service_date is not None:
            evidence.append(
                HealthEvidence(
                    label="Due date",
                    value=str(service_reminder.next_service_date),
                )
            )
        if service_reminder.next_service_odometer is not None:
            evidence.append(
                HealthEvidence(
                    label="Due odometer",
                    value=str(service_reminder.next_service_odometer),
                )
            )
        signals.append(
            HealthSignal(
                id="service_overdue",
                kind="service_overdue",
                urgency="critical",
                title="Service overdue",
                detail="; ".join(bits) or "Next service target has passed.",
                confidence="high",
                evidence=evidence,
                href_hint="service",
            )
        )
    elif not muted and service_reminder.status == "soon":
        bits = []
        if service_reminder.days_until is not None:
            bits.append(f"{service_reminder.days_until} day(s) left")
        if service_reminder.km_until is not None:
            bits.append(f"{service_reminder.km_until} km left")
        signals.append(
            HealthSignal(
                id="service_soon",
                kind="service_soon",
                urgency="high",
                title="Service coming up",
                detail="; ".join(bits) or "Next service is soon.",
                confidence="high",
                evidence=[],
                href_hint="service",
            )
        )

    for doc in document_reminders:
        if doc.status == "expired":
            urgency = "critical"
            title = f"{doc.display_label} expired"
            detail = f"{abs(doc.days_until)} day(s) ago"
            kind = "document_expired"
        else:
            urgency = "high"
            title = f"{doc.display_label} expires soon"
            detail = f"{doc.days_until} day(s) left"
            kind = "document_soon"
        evidence = []
        if doc.identifier:
            evidence.append(HealthEvidence(label="ID", value=doc.identifier))
        evidence.append(
            HealthEvidence(label="Expiry", value=str(doc.expiry_date))
        )
        signals.append(
            HealthSignal(
                id=f"document_{doc.id}",
                kind=kind,
                urgency=urgency,  # type: ignore[arg-type]
                title=title,
                detail=detail,
                confidence="high",
                evidence=evidence,
                href_hint="documents",
            )
        )

    if prediction.source == "catalog_estimate":
        evidence = [
            HealthEvidence(label="Source", value="maintenance catalog"),
        ]
        if prediction.matched_task:
            evidence.append(
                HealthEvidence(label="Task", value=prediction.matched_task)
            )
        signals.append(
            HealthSignal(
                id="service_prediction",
                kind="service_prediction",
                urgency="medium",
                title="Catalog-based next service",
                detail=prediction.detail,
                confidence="medium" if riding_rate else "low",
                evidence=evidence,
                href_hint="service",
            )
        )

    if mileage.trend == "down":
        signals.append(
            HealthSignal(
                id="mileage_decline",
                kind="mileage_decline",
                urgency="medium",
                title="Mileage looking worse",
                detail=mileage.detail,
                confidence="medium",
                evidence=[
                    HealthEvidence(
                        label="Recent avg",
                        value=f"{mileage.recent_avg} km/l",
                    ),
                    HealthEvidence(
                        label="Earlier avg",
                        value=f"{mileage.earlier_avg} km/l",
                    ),
                    HealthEvidence(
                        label="Samples",
                        value=str(mileage.sample_n),
                    ),
                ],
                href_hint="analytics",
            )
        )

    if fill_ups < 3:
        signals.append(
            HealthSignal(
                id="thin_history",
                kind="thin_history",
                urgency="low",
                title="Not enough history yet",
                detail=(
                    "Log a few more fill-ups so RideCare can estimate riding "
                    "rate and mileage trends honestly."
                ),
                confidence="insufficient",
                evidence=[
                    HealthEvidence(label="Fill-ups", value=str(fill_ups)),
                ],
                href_hint="fuel",
            )
        )

    if cost.confidence != "insufficient" and cpk is not None:
        signals.append(
            HealthSignal(
                id="cost_per_km",
                kind="cost_per_km",
                urgency="low",
                title=f"₹{cpk}/km ownership cost",
                detail=cost.detail,
                confidence=cost.confidence,  # type: ignore[arg-type]
                evidence=[
                    HealthEvidence(label="Km driven", value=str(kilometers)),
                    HealthEvidence(label="Fill-ups", value=str(fill_ups)),
                ],
                href_hint="analytics",
            )
        )

    urgency_rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "none": 4,
    }
    signals.sort(key=lambda s: (urgency_rank.get(s.urgency, 9), s.id))

    if muted:
        # Mute only suppresses nags — still recommend a useful next step when we have one.
        action_kinds = {"mileage_decline", "thin_history"}
    else:
        action_kinds = {
            "service_overdue",
            "service_soon",
            "document_expired",
            "document_soon",
            "mileage_decline",
            "thin_history",
        }

    recommended: RecommendedAction | None = None
    for signal in signals:
        if signal.kind in action_kinds:
            recommended = RecommendedAction(
                kind=signal.kind,
                title=signal.title,
                reason=signal.detail,
                urgency=signal.urgency,
                href_hint=signal.href_hint or "vehicle",
                confidence=signal.confidence,
            )
            break

    if recommended is None:
        if muted:
            recommended = RecommendedAction(
                kind="all_clear",
                title="Good to ride",
                reason="Reminders are off for this bike — schedule facts stay below.",
                urgency="none",
                href_hint="vehicle",
                confidence="high",
            )
        else:
            recommended = RecommendedAction(
                kind="all_clear",
                title="Good to ride",
                reason="No urgent service or document action right now.",
                urgency="none",
                href_hint="vehicle",
                confidence="high",
            )

    return VehicleHealthResponse(
        vehicle_id=vehicle.id,
        reminders_muted=muted,
        recommended_action=recommended,
        signals=signals,
        service_prediction=prediction,
        mileage=mileage,
        cost=cost,
    )
