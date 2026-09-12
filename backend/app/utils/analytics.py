"""Shared cost-per-km math for analytics and garage compare."""

from app.utils.numbers import round_2


def km_driven(baseline_odometer: float, live_odometer: float) -> float:
    """Kilometers logged since the vehicle baseline (2 decimal places)."""
    return round_2(max(float(live_odometer) - float(baseline_odometer), 0.0))


def round_money(value: float) -> float:
    return round_2(value)


def cost_per_km(spend: float, kilometers: float) -> float | None:
    """₹ per km, or None when distance is zero."""
    if kilometers <= 0:
        return None
    return round_money(spend / kilometers)
