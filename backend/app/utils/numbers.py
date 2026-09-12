"""Shared 2-decimal rounding for money, odometer, liters, and mileage."""


def round_2(value: float) -> float:
    """Round continuous vehicle metrics to two decimal places."""
    return round(float(value), 2)
