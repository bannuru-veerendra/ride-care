"""Shared cost-per-km math for analytics and garage compare."""


def km_driven(baseline_odometer: int, live_odometer: int) -> int:
    """Kilometers logged since the vehicle baseline."""
    return max(int(live_odometer) - int(baseline_odometer), 0)


def round_money(value: float) -> float:
    return round(float(value), 2)


def cost_per_km(spend: float, kilometers: int) -> float | None:
    """₹ per km, or None when distance is zero."""
    if kilometers <= 0:
        return None
    return round_money(spend / kilometers)
