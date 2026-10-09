"""Ranked health signals and the single recommended action."""

from __future__ import annotations

from app.schemas.vehicle import (
    CostHealth,
    DocumentReminder,
    HealthEvidence,
    HealthSignal,
    MileageHealth,
    RecommendedAction,
    ServicePrediction,
    ServiceReminder,
)


def rank_health_signals(
    *,
    muted: bool,
    service_reminder: ServiceReminder,
    document_reminders: list[DocumentReminder],
    prediction: ServicePrediction,
    mileage: MileageHealth,
    riding_rate: float | None,
    fill_ups: int,
    cpk: float | None,
    cost: CostHealth,
    kilometers: float,
) -> tuple[list[HealthSignal], RecommendedAction]:
    """Build urgency-sorted signals and one next action."""
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

    assert recommended is not None
    return signals, recommended
